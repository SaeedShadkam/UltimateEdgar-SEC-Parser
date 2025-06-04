import re
import requests
from bs4 import BeautifulSoup
import time
from Levenshtein import distance as levenshtein_distance
import numpy as np
import pandas as pd
import random
import sys
import html5lib


Old_HTMLs = []
Not_Well_Parsed = []


Official_Items_10K = ["Item 1. Business.",
         "Item 1A. Risk Factors.",
         "Item 1B. Unresolved Staff Comments.",
         "Item 2. Property.",#This is not the official title
         "Item 2. Properties.",
         "Item 2. Description of Properties.", #This is not the official title
         "Item 3. Legal Proceedings.",
         "Item 4. Mine Safety Disclosures.",
         "Item 4. REMOVED AND RESERVED.", #Not official, some disclosures have it
         "Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities.",
         "Item 6. Selected Financial Data.",
         "Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.",
         "Item 7. management’s discussion and analysis or plan of operation",
         "Item 7A. Quantitative and Qualitative Disclosures about Market Risk.",
         "Item 8. Financial Statements and Supplementary Data.",
         "Item 9. Changes in and Disagreements with Accountants on Accounting and Financial Disclosure.",
         "Item 9A. Controls and Procedures.",
         "Item 9B. Other Information.",
         "item 10. Directors, Executive Officers and Corporate Governance",
         "Item 11. Executive Compensation.",
         "Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters.",
         "Item 13. Certain Relationships and Related Transactions, and Director Independence.",
         "Item 14. Principal Accountant Fees and Services.",
         "Item #. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS", #Some of the files have this one
         "Item 15. Exhibits."] #This should be the last item
Official_Items_important_words_10K = [['business'],
         ['risk', 'factors'],
         ['unresolved', 'staff', 'comments'],
         ['property'],
         ['properties'],
         ['description', 'properties'],
         ['legal', 'proceedings'],
         ['mine', 'safety', 'disclosures'],
         ['removed', 'reserved'],
         ['market', 'registrant', 'common', 'equity', 'related', 'stockholder', 'matters', 'issuer', 'purchases', 'securities'],
         ['selected', 'financial', 'data'],
         ['management', 'discussion', 'analysis', 'financial', 'condition', 'results', 'operations'],
         ['management', 'discussion', 'analysis', 'plan', 'operation'],
         ['quantitative', 'qualitative', 'disclosures', 'market', 'risk'],
         ['financial', 'statements', 'supplementary', 'data'],
         ['changes', 'disagreements', 'accountants', 'accounting', 'financial', 'disclosure'],
         ['controls', 'procedures'],
         ['other', 'information'],
         ['directors', 'executive', 'officers', 'corporate', 'governance'],
         ['executive', 'compensation'],
         ['security', 'ownership', 'certain', 'beneficial', 'owners', 'management', 'related', 'stockholder', 'Mmatters'],
         ['certain', 'relationships', 'related', 'transactions', 'director', 'independence'],
         ['principal', 'accountant', 'fees', 'services'],
         ['submission', 'matters', 'vote', 'security', 'holders'],
         ['exhibits'],
         ['management', 'discussion', 'analysis', 'financial', 'condition', 'results', 'operations'],
         ['quantitative', 'qualitative', 'disclosures', 'market', 'risk'],
         ['controls', 'procedures'],
         ['legal', 'proceedings'],
         ['risk', 'factors'],
         ['unregistered', 'sales', 'equity', 'securities', 'proceeds'],
         ['defaults', 'upon', 'senior', 'securities'],
         ['mine', 'safety', 'disclosures'],
         ['other', 'information'],
         ['exhibits'],
         ['removed', 'reserved'],
         ['submission', 'mattersto', 'vote', 'security', 'holders'],
         ['changes', 'securities', 'proceeds', 'issuer', 'purchases', 'equity', 'securities'],
         ['condensed', 'consolidated', 'financial', 'statements'],
         ['issuer', 'purchases', 'equity', 'securities'],
         ['management', 'discussion', 'analysis']]

Official_Items = ["Item 1. Financial Statements.",
         "Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations.",
         "Item 3. Quantitative and Qualitative Disclosures About Market Risk.",
         "Item 4. Controls and Procedures.",
         "Item 1. Legal Proceedings.",
         "Item 1A. Risk Factors.",
         "Item 2. Unregistered Sales of Equity Securities and Use of Proceeds.",
         "Item 3. Defaults Upon Senior Securities.",
         "Item 4. Mine Safety Disclosures.",
         "Item 5. Other Information.",
         "Item 6. Exhibits.",
         "item 9. Removed And Reserved", # Some Documents have this item as well, shouldnt be included though
         "ITEM 9. SUBMISSION OF MATTERS TO A VOTE OF SECURITY HOLDERS", # Some Documents have this item as well, shouldnt be included though
         "ITEM 9. Changes in Securities and Use of Proceeds and Issuer Purchases of Equity Securities",
         "item 1. condensed consolidated financial statements",
         "Item 9. ISSUER PURCHASES OF EQUITY SECURITIES",# Some Documents have this item instead, shouldnt be included though
         "Item 2. Management's Discussion and Analysis"]

Official_Items_important_words = [['financial', 'statements'],
         ['management', 'discussion', 'analysis', 'financial', 'condition', 'results', 'operations'],
         ['quantitative', 'qualitative', 'disclosures', 'market', 'risk'],
         ['controls', 'procedures'],
         ['legal', 'proceedings'],
         ['risk', 'factors'],
         ['unregistered', 'sales', 'equity', 'securities', 'proceeds'],
         ['defaults', 'upon', 'senior', 'securities'],
         ['mine', 'safety', 'disclosures'],
         ['other', 'information'],
         ['exhibits'],
         ['removed', 'reserved'],
         ['submission', 'mattersto', 'vote', 'security', 'holders'],
         ['changes', 'securities', 'proceeds', 'issuer', 'purchases', 'equity', 'securities'],
         ['condensed', 'consolidated', 'financial', 'statements'],
         ['issuer', 'purchases', 'equity', 'securities'],
         ['management', 'discussion', 'analysis']]


def Remove_DuplicatedItems(Var, indices):
  for i in reversed(indices):
    del Var[i]
  return Var
def Find_DuplicatedItems_index(Var):
  oc_set = set()
  res = []
  for idx, val in enumerate(Var):
      if val not in oc_set:
          oc_set.add(val)
      else:
          res.append(idx)
  return  res


class Disclosure_10K():
  '''This class does almost everything. It makes an instance from each SEC document and does the pre-processing required on the instance and
  at the end adds the relevant information to the instance!'''

  def __init__(self, cik, TXT_Address, HTML_Address, Company_Name, Form_Type, Date_Filed):
    global Old_HTMLs
    global Not_Well_Parsed
    global String_Not_Available
    self.cik = cik
    prefix = "https://www.sec.gov/Archives/"
    self.TXT_Address = prefix + TXT_Address
    self.HTML_Address = prefix + HTML_Address
    self.Company_Name = Company_Name
    self.Form_Type = Form_Type
    self.Date_Filed = Date_Filed
    self.debug = False #Turning on this variable, enters the code into the debugign mode which prints out all the necessary information to make sure that the parsing goes well
    self.print_removed_tables = False
    self.Name = self.Company_Name + '_' + str(self.cik)
    self.Name = self.Name.replace('/', '')
    self.corrupted = False
    self.State = 'Fine'

  def Propreties(self):
    '''This function prints out a summary about the specific disclosure instance'''
    print(f'This file is for \033[94m"{self.Company_Name}"\033[0m with the cik \033[94m"{self.cik}"\033[0m, which has been filed on \033[94m"{self.Date_Filed}"\033[0m,')
    print(f'here is the link to the html source {self.HTML_Address},')
    print(f'and to the text file of the html code {self.TXT_Address}')
    print('----------------------------------------------------------')

    Title_Name = f'This file is for "{self.Company_Name}" with the cik "{self.cik}", which has been filed on "{self.Date_Filed}",<br>'
    Title_Name += f'here is the <a href={self.HTML_Address}>link</a> to the html source,<br>'
    Title_Name += f'and to the <a href={self.TXT_Address}>text file</a> of the html code<br>'

    self.Title_Name = Title_Name

  @classmethod
  def Initializer(cls, observation: pd.Series)->'Disclosure':
    return cls(observation.cik, observation.TXTAddress, observation.DisclosureAddress, observation.CompanyName, observation.FormType, observation.DateFiled)

  def Load(self):
    '''This function downloads the html (.txt) code and parse it Employing beautifulsoup'''
    url = self.TXT_Address
    response = requests.get(url, headers={'User-Agent': 'Example Contact (email@example.com)'})
    #print('Downloading the flie ....')
    self.Text = response.text
    try:
      self.soup = BeautifulSoup(self.Text, 'html.parser')
    except:
      if self.debug:
        print('\033[93m', 'Using html5lib ....')
      self.soup = BeautifulSoup(self.Text, 'html5lib') #lxml-xml: This one is super fast, mess with dome files though:https://www.sec.gov/Archives/edgar/data/820096/0000820096-13-000005.txt
                                                      #html5lib

    #self.Text = str(self.soup) #Makes python Crash
    #print('DONE!')
    #time.sleep(0.5)
    #output.clear()

  def Remove_Tables(self):


    self.number_of_tables =  len(self.soup.find_all('table'))
    self.total_table_removed = 0

    self.Remove_Tables_hreflinks()
    self.Remove_Tables_Color_html()
    self.Remove_Tables_Color_css()
    self.Remove_Tables_Numerical()

    #self.Text = str(self.soup)
    try:
      self.Text = str(self.soup)
      if self.debug:
        print(f'Number of Talbes eliminated: {self.total_table_removed} Out of: {self.number_of_tables}')
    except:
      A = str()
      for i in self.soup.find_all('html'):
        A += str(i)
      self.Text = A
      if self.debug:
        print(f'Number of Talbes eliminated: {self.total_table_removed} Out of: {self.number_of_tables}')
      #String_Not_Available.append(self)
      ##self.State = 'String Not Available'
      #self.corrupted = True

  def Remove_Tables_hreflinks(self):
    '''This function removes a table if it contains an href link, which indicates it is the table of contents.
    As a side bonus, it also removes the phrase "table of contents" within the text (at the end of each page there is sometimes a link to the table of contents).'''

    regex = '\s*table\s*of\s*contents'
    for element in self.soup.find_all('a', string=re.compile(regex, re.IGNORECASE)):
      element.decompose()

    regex = '\A#' # This means this is a link to a another section of the document (Not a link to a website or etc)
    elements = self.soup.find_all('a')
    j = 0
    i = 0
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if re.search(regex, element.attrs['href']):
          if element.find_parent('table'):
            if self.print_removed_tables:
              #print(element.find_parent('table').get_text())
              time.sleep(3)
              #output.clear()
            element.find_parent('table').decompose()
            elements = self.soup.find_all('a')
            i -= 1
            j += 1
      except:
        i += 1

    self.total_table_removed += j
    if self.debug:
      print(f'Number of tables removed(Table_Remover_hreflinks) : {j}')

    return
  def Remove_Tables_Numerical(self):

    #Dont add ( to the regex, it would remove many notes under the tables
    regex = '\A\s*($)*\(*\s*\d+,*\d*'
    number_of_eliminated_tables = 0


    for table in self.soup.find_all('table'):
      only_numerical_counter = 0
      for element in table.find_all('td'):
        if element.find(string=re.compile(regex, re.IGNORECASE)):
          only_numerical_counter +=1
      if only_numerical_counter>1:
        if self.print_removed_tables:
          #print(table.get_text())
          time.sleep(3)
          #output.clear()
        table.extract()
        number_of_eliminated_tables += 1
    if self.debug:
      print(f'Number of Talbes eliminated(Table_Remover_Numerical): {number_of_eliminated_tables}')
    self.total_table_removed += number_of_eliminated_tables
    return
  def Remove_Tables_Color_css(self):
    '''This table Removes any colored table if the coloring is done with CSS codes'''
    '''Only Numerical Tables are colored'''

    i = 0
    j = 0

    elements = self.soup.select("[style*='background-color:']")
    white_background_elements = list(set(self.soup.select("[style*='background-color:#ffffff']") + self.soup.select("[style*='background-color:#FFFFFF']")))

    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element not in white_background_elements:
          if self.print_removed_tables:
            #print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.select("[style*='background-color:']")
          i -= 1
          j += 1
      except:
        i += 1

    self.total_table_removed += j
    if self.debug:
      print(f'Number of tables removed(Table_Remover_Color_css): {j}')

    return
  def Remove_Tables_Color_html(self):
    '''This table Removes any colored table if the coloring is done with HTML codes'''
    '''Only Numerical Tables are colored'''
    i = 0
    j = 0
    elements = self.soup.find_all('tr')
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element.attrs['bgcolor'] != '#ffffff' and element.attrs['bgcolor'] != '#FFFFFF':
          if self.print_removed_tables:
            #print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.find_all('tr')
          i -= 1
          j += 1
      except:
        i += 1

    i = 0
    elements = self.soup.find_all('td')
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element.attrs['bgcolor'] != '#ffffff' and element.attrs['bgcolor'] != '#FFFFFF':
          if self.print_removed_tables:
            print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.find_all('td')
          i -= 1
          j += 1
      except:
        i += 1
    if self.debug:
      print(f'Number of tables removed(Table_Remover_Color_html) : {j}')
    self.total_table_removed += j
    return

  #Problem: "items affecting comparability"This is a new section in a document and captured as a section!Maybe we need to check for specific words to be present in the string
  #https://www.sec.gov/Archives/edgar/data/1138118/0001193125-16-764008-index.html
  def Section_Finder_html(self):
    '''This funtion Identifies any section that starts with the word item
    Then it calls another funtion named Item_Matcher()
    It also uses another function named clean_element_texts, which only cleans the text'''

    number_of_neighbors = 100
    regex = "\A\s*i{0,1}tem[^a-zA-Z]"
    regex = "\A\s*i{0,1}tem[^a-zA-Z]*" #Improved Version?
    elements = []
    elements_texts = []

    for element in self.soup.find_all(string=re.compile(regex, re.IGNORECASE)):
      element_text_neighbors = element.find_parent().get_text()
      last_text = element_text_neighbors

      for count, neighbor_element in enumerate(element.find_parent().next_elements):

        if count>number_of_neighbors:
          break
        if str(type(neighbor_element)) == "<class 'bs4.element.ProcessingInstruction'>":
          continue

        if str(type(neighbor_element)) == "<class 'bs4.element.Comment'>":
          continue
        elif str(type(neighbor_element)) == "<class 'bs4.element.NavigableString'>":
          text = neighbor_element
          text = re.sub("\A\s*" , "", text)
          text = re.sub("\s*\Z" , "", text)
          if (last_text!=text) and (not str.isspace(text)) and (text):
            last_text = text
            element_text_neighbors += ' ' + last_text

        elif str(type(neighbor_element)) == "<class 'bs4.element.Doctype'>":
          continue

        else:
          text = neighbor_element.get_text()
          text = re.sub("\A\s*" , "", text)
          text = re.sub("\s*\Z" , "", text)

          if (last_text !=text) and (not str.isspace(text)) and (text):
            last_text = text
            element_text_neighbors += ' ' + last_text



      elements.append(element.find_parent())
      elements_texts.append(self.Clean_Element_Texts(element_text_neighbors[:200]))

    self.elements = elements
    self.elements_texts = elements_texts
    self.Item_Matcher(elements_texts, Official_Items_10K)

    #In Some disclosures, they put the same section title, multiple times (https://www.sec.gov/Archives/edgar/data/1364742/000119312507240559/d10q.htm#toc68549_2)
    # Item 1.	Financial Statements and Item 1.	Financial Statements (continued)
    # So, I remove duplicated items from element and true element lists
    indices = Find_DuplicatedItems_index(self.True_Items)
    self.True_Items = Remove_DuplicatedItems(self.True_Items, indices)
    self.elements = Remove_DuplicatedItems(self.elements, indices)


    self.Is_This_Old_html()
    return

  def Is_This_Old_html(self):

    if (self.total_table_removed == 0):
      Old_HTMLs.append(self)
      self.State = 'Old'
      self.corrupted = True
      #print('\033[93m', 'This file could not be parsed well!', '\033[0m')

    elif  ("Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations." not in self.True_Items):
      Not_Well_Parsed.append(self)
      self.State = 'Not_well_parsed'
      self.corrupted = True
      #print('\033[93m', 'This file could not be parsed well(Old HTML)!', '\033[0m')

  def Item_Matcher(self, suspected_item, suspected_match):
    True_Items = []
    Wrong_Items_Indices = []
    for count, text in enumerate(self.elements_texts):
      score = []
      Items_Title_texts = []
      for item in Official_Items_10K:
        text2 = item.lower().replace('.', '').replace("’s", '')

        text1 = re.sub("\s\s+" , " ", text)
        text1_words = text1.split()
        text1 = " ".join(sorted(set(text1_words), key=text1_words.index))
        text1 = ' '.join(text1.split(' ')[:len(text2.split(' '))+1]) # I consider one extra word to not lose any information because of mistaken whitespace
        if text2 == "Item 1. Business.".lower().replace('.', '').replace("’s", ''):
          if re.search('business', ' '.join(text1.split(' ')[:-1]), re.IGNORECASE):
            score.append(0)
          else:
            score.append(levenshtein_distance(text2, text1)/len(text2.split(' ')))
        else:
          score.append(levenshtein_distance(text2, text1)/len(text2.split(' ')))

        Items_Title_texts.append(text1)

        #if self.debug == True:
          #print(text2, '\\\\\\', text1, levenshtein_distance(text2, text1)/len(text2.split(' ')))


      min_index = score.index(min(score))

      if re.search('exhibit', text1, re.IGNORECASE):
        min_index = Official_Items_10K.index('Item 15. Exhibits.')

      result = self.Final_Item_Checker(Items_Title_texts[min_index], Official_Items_important_words_10K[min_index])

      if min_index== Official_Items_10K.index("Item 7. management’s discussion and analysis or plan of operation"):
        min_index = Official_Items_10K.index('Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations.')
      elif (min_index== Official_Items_10K.index("Item 2. Description of Properties.")) or (min_index== Official_Items_10K.index("Item 2. Property.")):
        min_index = Official_Items_10K.index('Item 2. Properties.')


      if result:
        True_Items.append(Official_Items_10K[min_index]) # I normalize the levenshtein_distance measure. Is it the best measure?
        if self.debug:
          print(Items_Title_texts[min_index],'\033[93m',  '||', result, '||', '\033[0m', Official_Items_10K[min_index])
          print("-------------------------")
      else:
        Wrong_Items_Indices.append(count)

    for i in reversed(Wrong_Items_Indices):
      if self.debug:
        print('These Items were removed because of the FInal Item Checker:')
        print(self.elements_texts[i])
        print('---')
        print(self.elements[i])
        print('******')
      del self.elements_texts[i]
      del self.elements[i]


    self.True_Items = True_Items
    return

  def Final_Item_Checker(self, suspected_item, suspected_match):
    correct_words = 0
    #print('####', suspected_match)

    for word in suspected_item.split():
      if word in suspected_match:
        correct_words += 1
      if (word == 'exhibit') and (suspected_match == ['exhibits']): #Sometimes it is exhibit rather than exhibitS
        correct_words += 1
    if (correct_words/len(suspected_match))>=0.5:
      return True
    if self.debug:
      print((correct_words/len(suspected_match)), suspected_item,  suspected_match)
    return False

  def Clean_Element_Texts(self, text):

    '''This function prepare elements to be compared to official_titles introduced by SEC'''
    text = text.replace("'s", "")
    text = text.replace("'S", "")
    text = text.replace("’S", "")
    text = text.replace("’s", "")
    text = text.replace("&apos;s", "")
    text = text.replace("&#39;s", "")
    text = text.replace("&quot;s", "")
    text = text.replace("&#34;s", "")
    text = text.replace("&apos;S", "")
    text = text.replace("&#39;S", "")
    text = text.replace("&quot;S", "")
    text = text.replace("&#34;S", "")
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ')
    text = re.sub('[^A-Za-z0-9\s]+', ' ', text)
    text = re.sub("\s\s+" , " ", text)
    text = text.lower()
    return text

  def Section_text_Finder(self):

    Failed_elements = []

    if self.corrupted:
      return

    start_indices = []
    sections_text = []
    for element_number, element in enumerate(self.elements):
      #print(self.elements.index(element), len(start_indices))
      number_of_next_elements = 10
      number_of_parents = 6
      for i in range(number_of_parents):

        if i == number_of_parents-1:
          if self.debug:
              print(f"Could Not FInd the Section {element_number} suitable REGEX!")
          Failed_elements.append(element_number)
          break

        regex = str(element)
        regex = regex.replace('(', "\(")
        regex = regex.replace(')', "\)")
        regex = regex.replace('+', "\+")
        regex = re.sub('\[', '\\[', regex)
        if len(regex)>1000:
          #print(f"Could Not FInd Section {element_number} suitable REGEX!")
          Failed_elements.append(element_number)
          break

        if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
          start_indices.append(re.search(regex, self.Text, re.IGNORECASE).span()[0])
          break
        previous_element = str(element)
        try:
          for count, j in enumerate(element.next_elements):
            if count==number_of_next_elements:
              break

            if str(j) not in previous_element:
              previous_element = str(j)
              previous_element = previous_element.replace('(', "\(")
              previous_element = previous_element.replace(')', "\)")
              previous_element = re.sub('\[', '\\[', previous_element) #THis line has not been tested properly (6/29/2022) Saeed
              regex += previous_element

              if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
                break

        except:
          continue

        if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
          start_indices.append(re.search(regex, self.Text, re.IGNORECASE).span()[0])
          break
        else:
          element = element.find_parent()


    regex1 = "\n\s*\d{1,2}\s*\n"
    regex2 = "part\s*II.{0,5}\s*.{0,5}other\s*information"
    regex3 = '\n{3,15}'


    if len(start_indices) != len(self.True_Items):
      self.corrupted = True
      Not_Well_Parsed.append(self)
      self.State = 'Not_well_parsed'
      return

    for i in range(len(start_indices)-1):
      try:
        section_soup = BeautifulSoup(self.Text[start_indices[i]:start_indices[i+1]], 'html.parser')
      except:
        section_soup = BeautifulSoup(self.Text[start_indices[i]:start_indices[i+1]], 'html5lib')

      This_Section_text = section_soup.get_text()
      This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
      This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
      This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
      sections_text.append(This_Section_text)

    try:
      section_soup = BeautifulSoup(self.Text[start_indices[i+1]:], 'html.parser')
    except:
      section_soup = BeautifulSoup(self.Text[start_indices[i+1]:], 'html5lib')

    This_Section_text = section_soup.get_text()
    This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
    This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
    This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
    sections_text.append(This_Section_text)

    # What if for financial statements, the title was not there?
    if Official_Items_10K[0] not in self.True_Items:
      self.True_Items.insert(0, Official_Items_10K[0])
      try:
        section_soup = BeautifulSoup(self.Text[:start_indices[0]], 'html.parser')
      except:
        section_soup = BeautifulSoup(self.Text[:start_indices[0]], 'html5lib')

      This_Section_text = section_soup.get_text()
      This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
      This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
      This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
      sections_text.insert(0, This_Section_text)

    self.start_indices = start_indices
    self.sections_text = sections_text

    if self.debug:
      for i in range(len(self.elements)):

        print('\033[93m', self.True_Items[i], '\033[0m')
        print(sections_text[i][:300])
        print('-\-\-\-\-\-\-')
        print(self.sections_text[i][-300:])

  def Save_File(self):
    if self.corrupted:

      with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.html', 'w') as writefile:
        writefile.write(str(self.State))
      '''
      with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.txt', 'w') as writefile:
        writefile.write(self.soup.get_text())
        '''
      return
    Name = '<article><header><h1>' + self.Title_Name + '</h1></header>'
    with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.html', 'w') as writefile:
      writefile.write(Name)

      for item in self.True_Items: #Table Of Contents
        writefile.write(f'<p>{item}<p>')

      for i in range(len(self.True_Items)-1):#Remove Exhibits
        writefile.write(f'<h1>{self.True_Items[i]}</h1>')
        writefile.write(f'<p>{self.sections_text[i]}<p>')
      writefile.write(f'<h1>{self.True_Items[i+1]}</h1>')
      if self.True_Items[i+1]!= "Item 15. Exhibits.":
        writefile.write(f'<p>{self.sections_text[i+1]}</p>')
      writefile.write('</article>')


    #with open(f'/content/drive/My Drive/sec-edgar-filings/{self.Name}.txt', 'w') as writefile:
    '''with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.txt', 'w') as writefile:
      writefile.write(f"Text Address:{self.TXT_Address}")
      writefile.write(f"HTML Address:{self.HTML_Address}")
      for i in range(len((self.True_Items))-1):
        writefile.write('\n-------------------------------------------------------\n')
        writefile.write(self.True_Items[i])
        writefile.write('\n')
        writefile.write(self.sections_text[i])
      writefile.write('\n-------------------------------------------------------\n')
      writefile.write(self.True_Items[i+1])
      if self.True_Items[i+1]!= 'Item 6. Exhibits.':
        writefile.write(f'<p>{self.sections_text[i+1]}</p>')'''

class Disclosure():
  '''This class does almost everything. It makes an instance from each SEC document and does the pre-processing required on the instance and
  at the end adds the relevant information to the instance!'''

  def __init__(self, CIK, TXT_Address, HTML_Address, Company_Name, Form_Type, Date_Filed):
    global Old_HTMLs
    global Not_Well_Parsed
    global String_Not_Available
    self.CIK = CIK
    prefix = "https://www.sec.gov/Archives/"
    self.TXT_Address = prefix + TXT_Address
    self.HTML_Address = prefix + HTML_Address
    self.Company_Name = Company_Name
    self.Form_Type = Form_Type
    self.Date_Filed = Date_Filed
    self.debug = False #Turning on this variable, enters the code into the debugign mode which prints out all the necessary information to make sure that the parsing goes well
    self.print_removed_tables = False
    self.Name = self.Company_Name + '_' + str(self.CIK)
    self.Name = self.Name.replace('/', '')
    self.corrupted = False
    self.State = 'Fine'

  def Propreties(self):
    '''This function prints out a summary about the specific disclosure instance'''
    print(f'This file is for \033[94m"{self.Company_Name}"\033[0m with the CIK \033[94m"{self.CIK}"\033[0m, which has been filed on \033[94m"{self.Date_Filed}"\033[0m,')
    print(f'here is the link to the html source {self.HTML_Address},')
    print(f'and to the text file of the html code {self.TXT_Address}')
    print('----------------------------------------------------------')

    Title_Name = f'This file is for "{self.Company_Name}" with the CIK "{self.CIK}", which has been filed on "{self.Date_Filed}",<br>'
    Title_Name += f'here is the <a href={self.HTML_Address}>link</a> to the html source,<br>'
    Title_Name += f'and to the <a href={self.TXT_Address}>text file</a> of the html code<br>'

    self.Title_Name = Title_Name

  @classmethod
  def Initializer(cls, observation: pd.Series)->'Disclosure':
    return cls(observation.cik, observation.TXTAddress, observation.DisclosureAddress, observation.CompanyName, observation.FormType, observation.DateFiled)

  def Load(self):
    '''This function downloads the html (.txt) code and parse it Employing beautifulsoup'''
    url = self.TXT_Address
    response = requests.get(url, headers={'User-Agent': 'Example Contact (email@example.com)'})
    #print('Downloading the flie ....')
    self.Text = response.text
    try:
      self.soup = BeautifulSoup(self.Text, 'html.parser')
    except:
      if self.debug:
        print('\033[93m', 'Using html5lib ....')
      self.soup = BeautifulSoup(self.Text, 'html5lib') #lxml-xml: This one is super fast, mess with dome files though:https://www.sec.gov/Archives/edgar/data/820096/0000820096-13-000005.txt
                                                      #html5lib

    #self.Text = str(self.soup) #Makes python Crash
    #print('DONE!')
    #time.sleep(0.5)
    #output.clear()

  def Remove_Tables(self):


    self.number_of_tables =  len(self.soup.find_all('table'))
    self.total_table_removed = 0

    self.Remove_Tables_hreflinks()
    self.Remove_Tables_Color_html()
    self.Remove_Tables_Color_css()
    self.Remove_Tables_Numerical()

    #self.Text = str(self.soup)
    try:
      A = str()
      for i in self.soup.find_all('html'):
        A += str(i)
      self.Text = A
      if self.debug:
        print(f'Number of Talbes eliminated: {self.total_table_removed} Out of: {self.number_of_tables}')
    except:
      String_Not_Available.append(self)
      self.State = 'String Not Available'
      self.corrupted = True


  def Remove_Tables_hreflinks(self):
    '''This function removes a table if it contains an href link, which indicates it is the table of contents.
    As a side bonus, it also removes the phrase "table of contents" within the text (at the end of each page there is sometimes a link to the table of contents).'''

    regex = '\s*table\s*of\s*contents'
    for element in self.soup.find_all('a', string=re.compile(regex, re.IGNORECASE)):
      element.decompose()

    regex = '\A#' # This means this is a link to a another section of the document (Not a link to a website or etc)
    elements = self.soup.find_all('a')
    j = 0
    i = 0
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if re.search(regex, element.attrs['href']):
          if element.find_parent('table'):
            if self.print_removed_tables:
              #print(element.find_parent('table').get_text())
              time.sleep(3)
              #output.clear()
            element.find_parent('table').decompose()
            elements = self.soup.find_all('a')
            i -= 1
            j += 1
      except:
        i += 1

    self.total_table_removed += j
    #print(f'Number of tables removed(Table_Remover_hreflinks) : {j}')

    return
  def Remove_Tables_Numerical(self):

    #Dont add ( to the regex, it would remove many notes under the tables
    regex = '\A\s*($)*\(*\s*\d+,*\d*'
    number_of_eliminated_tables = 0


    for table in self.soup.find_all('table'):
      only_numerical_counter = 0
      for element in table.find_all('td'):
        if element.find(string=re.compile(regex, re.IGNORECASE)):
          only_numerical_counter +=1
      if only_numerical_counter>1:
        if self.print_removed_tables:
          #print(table.get_text())
          time.sleep(3)
          #output.clear()
        table.extract()
        number_of_eliminated_tables += 1
    #print(f'Number of Talbes eliminated(Table_Remover_Numerical): {number_of_eliminated_tables}')
    self.total_table_removed += number_of_eliminated_tables
    return
  def Remove_Tables_Color_css(self):
    '''This table Removes any colored table if the coloring is done with CSS codes'''
    '''Only Numerical Tables are colored'''

    i = 0
    j = 0

    elements = self.soup.select("[style*='background-color:']")
    white_background_elements = list(set(self.soup.select("[style*='background-color:#ffffff']") + self.soup.select("[style*='background-color:#FFFFFF']")))

    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element not in white_background_elements:
          if self.print_removed_tables:
            #print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.select("[style*='background-color:']")
          i -= 1
          j += 1
      except:
        i += 1

    self.total_table_removed += j
    #print(f'Number of tables removed(Table_Remover_Color_css): {j}')

    return
  def Remove_Tables_Color_html(self):
    '''This table Removes any colored table if the coloring is done with HTML codes'''
    '''Only Numerical Tables are colored'''
    i = 0
    j = 0
    elements = self.soup.find_all('tr')
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element.attrs['bgcolor'] != '#ffffff' and element.attrs['bgcolor'] != '#FFFFFF':
          if self.print_removed_tables:
            #print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.find_all('tr')
          i -= 1
          j += 1
      except:
        i += 1

    i = 0
    elements = self.soup.find_all('td')
    while i<len(elements):
      element = elements[i]
      try:
        i += 1
        if element.attrs['bgcolor'] != '#ffffff' and element.attrs['bgcolor'] != '#FFFFFF':
          if self.print_removed_tables:
            print(element.find_parent('table').get_text())
            time.sleep(3)
            #output.clear()
          element.find_parent('table').decompose()
          elements = self.soup.find_all('td')
          i -= 1
          j += 1
      except:
        i += 1

    #print(f'Number of tables removed(Table_Remover_Color_html) : {j}')
    self.total_table_removed += j
    return

  #Problem: "items affecting comparability"This is a new section in a document and captured as a section!Maybe we need to check for specific words to be present in the string
  #https://www.sec.gov/Archives/edgar/data/1138118/0001193125-16-764008-index.html
  def Section_Finder_html(self):
    '''This funtion Identifies any section that starts with the word item
    Then it calls another funtion named Item_Matcher()
    It also uses another function named clean_element_texts, which only cleans the text'''

    number_of_neighbors = 100
    regex = "\A\s*i{0,1}tem[^a-zA-Z]"
    regex = "\A\s*i{0,1}tem[^a-zA-Z]*" #Improved Version?
    elements = []
    elements_texts = []

    for element in self.soup.find_all(string=re.compile(regex, re.IGNORECASE)):
      element_text_neighbors = element.find_parent().get_text()
      last_text = element_text_neighbors

      for count, neighbor_element in enumerate(element.find_parent().next_elements):

        if count>number_of_neighbors:
          break
        if str(type(neighbor_element)) == "<class 'bs4.element.ProcessingInstruction'>":
          continue

        if str(type(neighbor_element)) == "<class 'bs4.element.Comment'>":
          continue
        elif str(type(neighbor_element)) == "<class 'bs4.element.NavigableString'>":
          text = neighbor_element
          text = re.sub("\A\s*" , "", text)
          text = re.sub("\s*\Z" , "", text)
          if (last_text!=text) and (not str.isspace(text)) and (text):
            last_text = text
            element_text_neighbors += ' ' + last_text

        elif str(type(neighbor_element)) == "<class 'bs4.element.Doctype'>":
          continue

        else:
          text = neighbor_element.get_text()
          text = re.sub("\A\s*" , "", text)
          text = re.sub("\s*\Z" , "", text)

          if (last_text !=text) and (not str.isspace(text)) and (text):
            last_text = text
            element_text_neighbors += ' ' + last_text



      elements.append(element.find_parent())
      elements_texts.append(self.Clean_Element_Texts(element_text_neighbors[:200]))

    self.elements = elements
    self.elements_texts = elements_texts
    self.Item_Matcher(elements_texts, Official_Items)

    #In Some disclosures, they put the same section title, multiple times (https://www.sec.gov/Archives/edgar/data/1364742/000119312507240559/d10q.htm#toc68549_2)
    # Item 1.	Financial Statements and Item 1.	Financial Statements (continued)
    # So, I remove duplicated items from element and true element lists
    indices = Find_DuplicatedItems_index(self.True_Items)
    self.True_Items = Remove_DuplicatedItems(self.True_Items, indices)
    self.elements = Remove_DuplicatedItems(self.elements, indices)


    self.Is_This_Old_html()
    return

  def Is_This_Old_html(self):

    if (self.total_table_removed == 0):
      Old_HTMLs.append(self)
      self.State = 'Old'
      self.corrupted = True
      #print('\033[93m', 'This file could not be parsed well!', '\033[0m')

    elif  (Official_Items[1] not in self.True_Items):
      Not_Well_Parsed.append(self)
      self.State = 'Not_well_parsed'
      self.corrupted = True
      #print('\033[93m', 'This file could not be parsed well(Old HTML)!', '\033[0m')

  def Item_Matcher(self, suspected_item, suspected_match):
    True_Items = []
    Wrong_Items_Indices = []
    for count, text in enumerate(self.elements_texts):
      score = []
      Items_Title_texts = []
      for item in Official_Items:
        text2 = item.lower().replace('.', '').replace("’s", '')

        text1 = re.sub("\s\s+" , " ", text)
        text1_words = text1.split()
        text1 = " ".join(sorted(set(text1_words), key=text1_words.index))
        text1 = ' '.join(text1.split(' ')[:len(text2.split(' '))+1]) # I consider one extra word to not lose any information because of mistaken whitespace
        Items_Title_texts.append(text1)
        score.append(levenshtein_distance(text2, text1)/len(text2.split(' ')))
        #if self.debug == True:
          #print(t1, '\\\\\\', text1, levenshtein_distance(text2, text1)/len(text2.split(' ')))

      min_index = score.index(min(score))

      if re.search('exhibit', text1, re.IGNORECASE): ## This has been tested on 10-K forms
        min_index = Official_Items.index('Item 6. Exhibits.')
      result = self.Final_Item_Checker(Items_Title_texts[min_index], Official_Items_important_words[min_index])

      if min_index== Official_Items.index('item 1. condensed consolidated financial statements'):
        min_index = Official_Items.index('Item 1. Financial Statements.')

      elif min_index== Official_Items.index("Item 2. Management's Discussion and Analysis"):
        min_index = Official_Items.index("Item 2. Management's Discussion and Analysis of Financial Condition and Results of Operations.")

      if result:
        True_Items.append(Official_Items[min_index]) # I normalize the levenshtein_distance measure. Is it the best measure?
        if self.debug:
          print(Items_Title_texts[min_index],'\033[93m',  '||', result, '||', '\033[0m', Official_Items[min_index])
          print("-------------------------")
      else:
        Wrong_Items_Indices.append(count)

    for i in reversed(Wrong_Items_Indices):
      if self.debug:
        print('These Items were removed because of the FInal Item Checker:')
        print(self.elements_texts[i])
        print('---')
        print(self.elements[i])
        print('******')
      del self.elements_texts[i]
      del self.elements[i]


    self.True_Items = True_Items
    return

  def Final_Item_Checker(self, suspected_item, suspected_match):
    correct_words = 0
    #print(suspected_item)
    for word in suspected_item.split():
      if word in suspected_match:
        correct_words += 1
      if (word == 'exhibit') and (suspected_match == ['exhibits']): #Sometimes it is exhibit rather than exhibitS
        correct_words += 1
    if (correct_words/len(suspected_match))>=0.5:
      return True
    return False

  def Clean_Element_Texts(self, text):

    '''This function prepare elements to be compared to official_titles introduced by SEC'''
    text = text.replace("'s", "")
    text = text.replace("'S", "")
    text = text.replace("’S", "")
    text = text.replace("’s", "")
    text = text.replace("&apos;s", "")
    text = text.replace("&#39;s", "")
    text = text.replace("&quot;s", "")
    text = text.replace("&#34;s", "")
    text = text.replace("&apos;S", "")
    text = text.replace("&#39;S", "")
    text = text.replace("&quot;S", "")
    text = text.replace("&#34;S", "")
    text = text.replace('\xa0', ' ')
    text = text.replace('\n', ' ')
    text = re.sub('[^A-Za-z0-9\s]+', ' ', text)
    text = re.sub("\s\s+" , " ", text)
    text = text.lower()
    return text

  def Section_text_Finder(self):

    Failed_elements = []

    if self.corrupted:
      return

    start_indices = []
    sections_text = []
    for element_number, element in enumerate(self.elements):
      #print(self.elements.index(element), len(start_indices))
      number_of_next_elements = 10
      number_of_parents = 6
      for i in range(number_of_parents):

        if i == number_of_parents-1:
          #print(f"Could Not FInd the Section {element_number} suitable REGEX!")
          Failed_elements.append(element_number)
          break

        regex = str(element)
        regex = regex.replace('(', "\(")
        regex = regex.replace(')', "\)")
        regex = regex.replace('+', "\+")
        regex = re.sub('\[', '\\[', regex)
        if len(regex)>1000:
          #print(f"Could Not FInd Section {element_number} suitable REGEX!")
          Failed_elements.append(element_number)
          break

        if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
          start_indices.append(re.search(regex, self.Text, re.IGNORECASE).span()[0])
          break
        previous_element = str(element)
        try:
          for count, j in enumerate(element.next_elements):
            if count==number_of_next_elements:
              break

            if str(j) not in previous_element:
              previous_element = str(j)
              previous_element = previous_element.replace('(', "\(")
              previous_element = previous_element.replace(')', "\)")
              previous_element = re.sub('\[', '\\[', previous_element) #THis line has not been tested properly (6/29/2022) Saeed
              regex += previous_element

              if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
                break

        except:
          continue

        if len(re.findall(regex, self.Text, re.IGNORECASE)) == 1:
          start_indices.append(re.search(regex, self.Text, re.IGNORECASE).span()[0])
          break
        else:
          element = element.find_parent()


    regex1 = "\n\s*\d{1,2}\s*\n"
    regex2 = "part\s*II.{0,5}\s*.{0,5}other\s*information"
    regex3 = '\n{3,15}'


    if len(start_indices) != len(self.True_Items):
      self.corrupted = True
      Not_Well_Parsed.append(self)
      self.State = 'Not_well_parsed'
      return

    for i in range(len(start_indices)-1):
      try:
        section_soup = BeautifulSoup(self.Text[start_indices[i]:start_indices[i+1]], 'html.parser')
      except:
        section_soup = BeautifulSoup(self.Text[start_indices[i]:start_indices[i+1]], 'html5lib')

      This_Section_text = section_soup.get_text()
      This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
      This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
      This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
      sections_text.append(This_Section_text)

    try:
      section_soup = BeautifulSoup(self.Text[start_indices[i+1]:], 'html.parser')
    except:
      section_soup = BeautifulSoup(self.Text[start_indices[i+1]:], 'html5lib')

    This_Section_text = section_soup.get_text()
    This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
    This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
    This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
    sections_text.append(This_Section_text)

    # What if for financial statements, the title was not there?
    if Official_Items[0] not in self.True_Items:
      self.True_Items.insert(0, Official_Items[0])
      try:
        section_soup = BeautifulSoup(self.Text[:start_indices[0]], 'html.parser')
      except:
        section_soup = BeautifulSoup(self.Text[:start_indices[0]], 'html5lib')

      This_Section_text = section_soup.get_text()
      This_Section_text = re.sub(regex1, '', string = This_Section_text, flags = re.IGNORECASE) #Remove Page Numbers
      This_Section_text = re.sub(regex2, '', string = This_Section_text, flags = re.IGNORECASE)
      This_Section_text = re.sub(regex3, '\n\n', string = This_Section_text, flags = re.IGNORECASE) #Remove Multiple New Line Commands
      sections_text.insert(0, This_Section_text)

    self.start_indices = start_indices
    self.sections_text = sections_text

    if self.debug:
      for i in range(len(self.elements)):

        print('\033[93m', self.True_Items[i], '\033[0m')
        print(sections_text[i][:300])
        print('-\-\-\-\-\-\-')
        print(self.sections_text[i][-300:])

  def Save_File(self):
    if self.corrupted:
      '''
      with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.html', 'w') as writefile:
        writefile.write(str(self.State))
      '''
      with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.txt', 'w') as writefile:
        writefile.write(self.soup.get_text())

      return
    '''Name = '<article><header><h1>' + self.Title_Name + '</h1></header>'
    with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.html', 'w') as writefile:
      writefile.write(Name)

      for item in self.True_Items: #Table Of Contents
        writefile.write(f'<p>{item}<p>')

      for i in range(len(self.True_Items)-1):#Remove Exhibits
        writefile.write(f'<h1>{self.True_Items[i]}</h1>')
        writefile.write(f'<p>{self.sections_text[i]}<p>')
      writefile.write(f'<h1>{self.True_Items[i+1]}</h1>')
      if self.True_Items[i+1]!= 'Item 6. Exhibits.':
        writefile.write(f'<p>{self.sections_text[i+1]}</p>')
      writefile.write('</article>')'''


    #with open(f'/content/drive/My Drive/sec-edgar-filings/{self.Name}.txt', 'w') as writefile:
    with open(f'/content/drive/My Drive/sec-edgar-filings/Size/500_Parsed_10Q/{self.Name}.txt', 'w') as writefile:
      writefile.write(f"Text Address:{self.TXT_Address}")
      writefile.write(f"HTML Address:{self.HTML_Address}")
      for i in range(len((self.True_Items))-1):
        writefile.write('\n-------------------------------------------------------\n')
        writefile.write(self.True_Items[i])
        writefile.write('\n')
        writefile.write(self.sections_text[i])
      writefile.write('\n-------------------------------------------------------\n')
      writefile.write(self.True_Items[i+1])
      if self.True_Items[i+1]!= 'Item 6. Exhibits.':
        writefile.write(f'<p>{self.sections_text[i+1]}</p>')

def paragraph_splitter(doc, max_words_document=500):

  par = []
  while len(doc.split())>max_words_document:
    # It checks for 10 sentence in a paragraph
    indicator = False
    for j in range(10):
      matches = re.finditer('\.', doc)
      for match in reversed(list(matches)):
        if len(doc[:match.span()[0]].split())<max_words_document:
          par.append(doc[:match.span()[1]])
          doc = doc[match.span()[1]:]
          indicator = True
          break

    if not indicator:
      #print("There is a senctence exceeding maximum word numbers!")
      # I need to randomely split the paragraph. I try to make one as long as possible paragraph
      # Then, I check for sentence in the rest of the paragraph
      matches = re.finditer('\s', doc)
      for match in reversed(list(matches)):
        if len(doc[:match.span()[0]].split())<max_words_document:
          par.append(doc[:match.span()[1]])
          doc = doc[match.span()[1]:]
          break
  par.append(doc)

  document = []
  for i in par:
    document.append(i)
  return document
