import pandas as pd
import time
from selenium import webdriver
import openpyxl
import numpy as np
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException

# 채널명이 들어있는 데이터
ch = pd.read_csv("./data/channel_qna.csv")
try:
    wb = openpyxl.load_workbook("result.xlsx")
except:
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.append(["추가일시","전체 인덱스","채널명","채널인덱스","글인덱스","댓글내용","좋아요"])
else:
    sheet = wb.active



# elements 리스트를 받아서 click되는 애들만 리스트로 반환

def interact(elements):
    arr_elements = np.array(elements)
    arr_can = [elements[i].is_displayed() for i in range(len(elements))]
    arr_can_elements = arr_elements[arr_can]
    return list(arr_can_elements)



# 유튜브 채널 접속

driver = webdriver.Chrome("./chromedriver")

driver.get("https://www.youtube.com/")

index = 0


for name in ch['channel'][44:]:

    ch_index = 0
    con_index = 0
    # 검색창에 채널 이름 입력 및 검색
    driver.find_element_by_css_selector("input#search").clear()
    driver.find_element_by_css_selector("input#search").send_keys(name)
    driver.find_element_by_css_selector("button#search-icon-legacy").click()
    time.sleep(3)

    # 채널 클릭
    # searchresult = driver.find_elements_by_xpath("//yt-formatted-string[@class='style-scope.ytd-channel-name' and contains(text(),'지현꿍')]")
    searchresult = interact(driver.find_elements_by_xpath("//yt-formatted-string[@class='style-scope ytd-channel-name' and contains(text(), name)]"))
    searchresult[0].click()
    time.sleep(3)

    #멤버십 구독 버튼 클릭
    member_button = interact(driver.find_elements_by_css_selector("yt-formatted-string.style-scope.yt-button-renderer.style-blue-text.size-default"))
    if len(member_button)!=0:
        interact(member_button)[0].click()

    # 커뮤니티 버튼 클릭,, 여기서 에러뜨는 경우 있음
    com_button = driver.find_elements_by_css_selector("div.tab-content.style-scope.paper-tab")
    com_button[3].click()
    time.sleep(4)

    print("커뮤니티 진입")

    # qna찾기 위해 끝까지 스크롤

    last_height = driver.execute_script("return document.documentElement.scrollHeight")
    while True:
        print("스크롤", end="")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        print(" 완료, 2초 대기")

        time.sleep(2)

        new_height = driver.execute_script("return document.documentElement.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height


    qna_cont = driver.find_elements_by_xpath("//*[contains(text(), 'QnA') or contains(text(), 'Q&A') or contains(text(), '큐엔에이') or contains(text(), '궁금한 점') or contains(text(), 'q&a') or contains(text(), 'Q/A') or contains(text(), '궁금하신') or contains(text(), '질문하나') or contains(text(), '큐앤에이')]")
    qna_can_cont = interact(qna_cont)

    ###창 넘어가는 qna글은 따로 리스트에 저장하기 위해 초기화
    new_view = []

    # 댓글 모두보기에 해당하는 qna글들만
    for qna_content in qna_can_cont:
        ###qna 게시글, 게시글의 댓글 접근
        qna = qna_content.find_element_by_xpath('../../../../../../..')

        try :
            # 댓글 모두보기버튼 찾아보기
            qna_com = qna.find_element_by_css_selector("paper-button.align-by-text.style-scope.ytd-backstage-comments-renderer")
        except NoSuchElementException:
            # 댓글 모두보기 버튼 없는 경우에 new view리스트에 그 버튼의 url 추가 (새창넘어가는 버튼임)
            new_view.append(qna.find_element_by_css_selector("a.yt-simple-endpoint.style-scope.ytd-button-renderer").get_attribute("href"))
            continue
        else:
            ###그 게시글의 댓글로 이동해서 클릭
            action = ActionChains(driver)
            action.move_to_element(qna_com).perform()
            qna_com.click()


        wait = 0
        ###그 게시글의 댓글 더보기 이동해서 클릭,, 그 qna글에 댓글 더보기가 더이상 없을 때까지 반복
        while True:
            try:
                qna_com_more = interact(qna.find_elements_by_css_selector("yt-formatted-string.style-scope.yt-next-continuation"))
                print("3초 대기")
                time.sleep(3)
                action = ActionChains(driver)
                action.move_to_element(qna_com_more[0]).perform()
                qna_com_more[0].click()
                wait = 0
            except:
                wait +=1
                print("더보기 없는 것으로 추정, 더 대기")
                if wait == 2:
                    print("2번 대기, break됨")
                    break
        print(qna_can_cont.index(qna_content)+1,"번째 qna글의 모든 댓글 완료")

    print("댓글들 접근 시작")

    container = driver.find_elements_by_css_selector("ytd-comment-renderer#comment")

    for comcont in container:

        try:  # 자세히보기 버튼 클릭 try
            comcont.find_element_by_css_selector("ytd-comment-renderer#comment span.more-button").click()
            comment = comcont.find_element_by_css_selector("ytd-comment-renderer#comment div#content").text

        except:
            comment = comcont.find_element_by_css_selector("ytd-comment-renderer#comment ytd-expander#expander").text

        like_text = comcont.find_element_by_css_selector("ytd-comment-renderer#comment span#vote-count-middle").text

        if (like_text == ""):  # like가 비어있다면 0개로 처리
            like_text = "0"
        like = like_text
        unit = ["천", "만"]
        for i in range(2):
            if unit[i] in like_text:
                like = str(int(float(like_text.replace(unit[i], "")) * int("100" + "0" * (i + 1))))

        print(like,comment)
        print("--------------")
        ch_index += 1
        index += 1

        # (["추가일시","전체 인덱스","채널명","채널인덱스","글인덱스","댓글내용","좋아요"])
        #try :
        sheet.append([time.strftime('%d %H:%M:%S', time.localtime(time.time())),index, name, ch_index, con_index, comment, like])
        #except: # 한 댓글 때문에 추가한 부분.. 이것때문에 느려지면 다른 방법 찾아야함
            #comment = comment.replace("\x00", "")
            #sheet.append([time.strftime('%d %H:%M:%S', time.localtime(time.time())), index, name, ch_index, con_index, comment, like])
    # print("==================")

    wb.save("result.xlsx")


    ### 새창에서 댓글 보이는 거 각각 접속 - 무한스크롤 포함, 댓글 읽기 포함
    for new in new_view:
        con_index+=1
        driver.get(new)

        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        while True:
            print("스크롤", end="")
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            print(" 완료, 2초 대기")

            time.sleep(2)

            new_height = driver.execute_script("return document.documentElement.scrollHeight")

            if new_height == last_height:
                break
            last_height = new_height

        print("댓글들 접근 시작")

        container = driver.find_elements_by_css_selector("ytd-comment-renderer#comment")

        for comcont in container:

            try:  # 자세히보기 버튼 클릭 try
                comcont.find_element_by_css_selector("ytd-comment-renderer#comment span.more-button").click()
                comment = comcont.find_element_by_css_selector("ytd-comment-renderer#comment div#content").text

            except:
                comment = comcont.find_element_by_css_selector("ytd-comment-renderer#comment ytd-expander#expander").text

            like_text = comcont.find_element_by_css_selector("ytd-comment-renderer#comment span#vote-count-middle").text

            if (like_text == ""):  # like가 비어있다면 0개로 처리
                like_text = "0"
            like = like_text
            unit = ["천", "만"]
            for i in range(2):
                if unit[i] in like_text:
                    like = str(int(float(like_text.replace(unit[i], "")) * int("100" + "0" * (i + 1))))

            print(like,comment)
            print("--------------")
            ch_index += 1
            index += 1

            # (["추가일시","전체 인덱스","채널명","채널인덱스","글인덱스","댓글내용","좋아요"])
            sheet.append([time.strftime('%d %H:%M:%S', time.localtime(time.time())),index, name, ch_index, con_index, comment, like])
        wb.save("result.xlsx")


