# login
#     POST https://open.kattis.com/login
#         data => user, token, script=true
# get submissions page by page
#     use binary search to get number of pages
#     https://open.kattis.com/users/{username}?page={page_number}
#     page is empty if "<tbody></tbody>" in body
#     extract submission id from page
# get individual submission using id from above if acc
#     get https://open.kattis.com/submissions/5049877/source/peragrams.py



import requests
from lxml import html
from slugify import slugify
import os
from console_progressbar import ProgressBar

USERNAME = "0xecho"
TOKEN = "0bb58720546cb70ce143e7ec68a0e91c64384307cadbd717ee1f2f1927baf938"
BASE_URL = "https://open.kattis.com"
LOGIN_URL = "https://open.kattis.com/login"
LOGOUT_URL = "https://open.kattis.com/logout"
PROFILE_URL = f"https://open.kattis.com/users/{USERNAME}"
SUBMISSION_URL = "https://open.kattis.com/submissions/"
MYCONTACT = "0xecho.proto-code.com"
_HEADERS = {
    "User-Agent": "kattis-submissions-downloader",
    "Contact": MYCONTACT,
}
PROFILE_PAGES_CACHE = {}
CORRECT_SUBMISSIONS = {}

try:
    ## HELPERS
    def get_profile_page(pagenum):
        if pagenum in PROFILE_PAGES_CACHE.keys():
            return PROFILE_PAGES_CACHE[pagenum]
        else:
            resp = main_session.get(PROFILE_URL + "?page=" + str(pagenum))
            PROFILE_PAGES_CACHE[pagenum] = resp
            return resp
    
    def isvalidpage(pagenum):
        resp = get_profile_page(pagenum)
        return not "<tbody></tbody>" in resp.text
        
    def parse_profile_page(document):
    
        tree = html.fromstring(document)
        table = tree.xpath("/html/body/div[1]/div/div[2]/section/table")[0]
        table_body = table.findall('tbody')[0]
        table_rows = table_body.getchildren()
        
        for table_row in table_rows:
            submission_id = table_row.attrib['data-submission-id']
            title_tag = table_row.getchildren()[2]
            problem_name = title_tag.getchildren()[0].text
            status_tag = table_row.getchildren()[3]
            status = status_tag.getchildren()[0].attrib['class']
            if status == "accepted":
                CORRECT_SUBMISSIONS[submission_id] = problem_name

        return 1 # temp val
    
    def get_and_save_submission(submission_id, problem_name):
        submision_page = main_session.get(SUBMISSION_URL + str(submission_id)).text
        tree = html.fromstring(submision_page)
        download_btn = tree.xpath("/html/body/div[1]/div/div[3]/section/div[2]/table/tbody/tr/td[4]/a[1]")[0]
        download_url = BASE_URL + download_btn.attrib["href"]
        file_name = download_btn.attrib["href"].split("/")[-1]
        submission_file = main_session.get(download_url)
        # TODO check if file exists and create new
        # TODO handle this better
        try:
            os.mkdir("Submissions")
        except:
            pass
        with open("Submissions/"+file_name, 'w') as f:
            f.write(submission_file.text)
        
        
    main_session = requests.Session()
    main_session.headers.update(_HEADERS)
    
    ## LOGIN
    
    login_data = {
        "user": USERNAME,
        "token": TOKEN,
        "script": "true",
    }
    
    resp = main_session.post(LOGIN_URL, data=login_data)
    
    if "Success" in resp.text:
        print("[+] Logged in Successfully")
        print("[+] Testing for number of pages")
    # print(resp.text)  ## LOGIN UNSUCESSFULL CHECK
    
    min_page_number = 1
    max_page_number = 100
    prev_min_page_number = 0
    
    while prev_min_page_number < min_page_number:
        current_page_number = (min_page_number + max_page_number)//2
        print("Trying page", current_page_number)
        if isvalidpage(current_page_number):
            prev_min_page_number = min_page_number 
            min_page_number = current_page_number
        else:
            max_page_number = current_page_number
    
    max_page_number = prev_min_page_number
    
    profile_pages = []
    
    for pagenum in range(1,max_page_number+1):
        profile_pages.append(get_profile_page(pagenum))
    
    for profile_page in profile_pages:        
        parse_profile_page(profile_page.text)
    
    num_of_correct = len(CORRECT_SUBMISSIONS)
    print("[+] Got", num_of_correct, "correct answers!")
    
    pbar = ProgressBar(total=num_of_correct,prefix='Donwloading', decimals=2, fill='*', zfill='_')
    count = 1
    for submission_id, problem_name in CORRECT_SUBMISSIONS.items():
        get_and_save_submission(submission_id, problem_name)
        pbar.print_progress_bar(count)
        count+=1
        
    
except KeyboardInterrupt:
    pass
main_session.get(LOGOUT_URL)
