import requests
import bs4
from time import sleep
import pandas as pd

BASEURL = 'http://collegecatalog.uchicago.edu/'
page = requests.get(BASEURL)
print("Sleeping")
sleep(3)
def get_programs_of_study_url(page):
    '''Given a PAGE, return a string containing a link to the str
    page linked in the html.
    '''
    soup = bs4.BeautifulSoup(page.text, features="html.parser")
    pagelink = soup.find_all("a")
    str_anchor = [a for a in pagelink if a.text == 'Programs of Study']
    link =str_anchor[0].attrs["href"]
    return BASEURL + link
def get_program_url(page):
    program_url_lst = []
    soup = bs4.BeautifulSoup(page.text, features = 'html.parser')
    program_list = soup.find('ul', id = '/thecollege/programsofstudy/').find_all('a')
    for program in program_list:
        link = program['href']
        program_url_lst.append(BASEURL + link)
    return program_url_lst

def get_courses_df(page):
    soup = bs4.BeautifulSoup(page.text, features = 'html.parser')
    courses = soup.find_all('div', class_ = ['courseblock main', 'courseblock subsequence'])
    for course in courses:
        course_number = course.find('strong').text.split('.')[0]
        if len(course_number) > 10:
            courses.remove(course)
    course_number_lst = [x.find('strong').text.replace('\xa0', ' ').split('.')[0] for x in courses]
    course_description_lst = [x.find('p', class_ = 'courseblockdesc').text.replace('\n', '') for x in courses]
    equivalent_courses_lst = []
    prerequisite_lst = []
    terms_offered_lst = []
    instructor_lst = []
    course_details = [x.find('p', class_='courseblockdetail').text.replace('\n', ' ') if x.find('p', class_ = 'courseblockdetail') else '' for x in courses]
    for detail in course_details:
        if 'Equivalent Course(s): ' in detail:
            splt = detail.split('Equivalent Course(s): ')
            equivalent_courses_lst.append(splt[1])
            splt = splt[:-1]
            detail = ''.join(splt)
        else:
            equivalent_courses_lst.append('')

        if 'Note(s): ' in detail:
            splt = detail.split('Note(s): ')
            splt = splt[:-1]
            detail = ''.join(splt)

        if 'Prerequisite(s): ' in detail:
            splt = detail.split('Prerequisite(s): ')
            prerequisite_lst.append(splt[1])
            splt = splt[:-1]
            detail = ''.join(splt)
        else:
            prerequisite_lst.append('')

        if 'Terms Offered: ' in detail:
            splt = detail.split('Terms Offered: ')
            terms_offered_lst.append(splt[1])
            splt = splt[:-1]
            detail = ''.join(splt)
        else:
            terms_offered_lst.append('')

        if 'Instructor(s): ' in detail:
            splt = detail.split('Instructor(s): ')
            instructor_lst.append(splt[1].replace('\xa0', ''))
        else:
            instructor_lst.append('')

    df= pd.DataFrame({
        'Course Number': course_number_lst,
        'Description': course_description_lst,
        'Terms Offered': terms_offered_lst,
        'Equivalent Courses': equivalent_courses_lst,
        'Prerequisites': prerequisite_lst,
        'Instructors': instructor_lst
    })
    return df

def deduplicate(df):
    classes_to_keep = set()
    seen_classes = set()
    for i, row in df.iterrows():
        course = row['Course Number']
        equivalent_courses = row['Equivalent Courses'].split(',')
        if course not in seen_classes and seen_classes.isdisjoint(equivalent_courses):
            classes_to_keep.add(course)
        seen_classes.update(equivalent_courses)
        seen_classes.add(course)
    return df[df['Course Number'].isin(classes_to_keep)]

def classes_by_department(df):
    classes = [x[:4] for x in df['Course Number']]
    unique_department = set(classes)
    department_dict = dict()
    for department in unique_department:
        department_dict[department] = classes.count(department)
    df = pd.DataFrame({
        'Department': department_dict.keys(),
        'Count': department_dict.values()
    })
    df = df.sort_values(by = 'Count', ascending=False)
    return df

def classes_by_quarter(df):
    classes = [x[:4] for x in df['Course Number']]
    quarters = ['Autumn', 'Winter', 'Spring']
    quarter_dict = dict()
    for quarter in quarters:
        quarter_dict[quarter] = sum([quarter in x for x in df['Terms Offered']])
    return quarter_dict

print("Sleeping")
sleep(3)
programs_of_study_page = requests.get(get_programs_of_study_url(page))
program_urls = get_program_url(programs_of_study_page)

program_pages = []
for url in program_urls:
    program_pages.append(requests.get(url))
    print("Sleeping")
    sleep(3)

courses_df = pd.DataFrame()
for pages in program_pages:
    df = get_courses_df(pages)
    courses_df = pd.concat([courses_df, df], axis = 0)
courses_df = courses_df.reset_index(drop = True)

deduplicated_df = deduplicate(courses_df)
department_count_df = classes_by_department(deduplicated_df)
quarter_count_df = classes_by_quarter(deduplicated_df)

print(quarter_count_df)
print('There are %d classes overall' % len(courses_df))
print('There are %d deduplicated classes overall' % len(deduplicated_df))

courses_df.to_csv('courses.csv', index=False)
deduplicated_df.to_csv('deduplicated.csv', index = False)
department_count_df.to_csv('department_count.csv', index = False)


