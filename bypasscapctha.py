from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import requests
import os
from bs4 import BeautifulSoup

delayTime = 2
audioToTextDelay = 10
filename = '1.mp3'
byPassUrl = 'https://tckimlik.nvi.gov.tr/Modul/TcKimlikNoDogrula'
googleIBMLink = 'https://speech-to-text-demo.ng.bluemix.net/'

option = webdriver.ChromeOptions()
option.add_argument('--disable-notifications')
option.add_argument("--mute-audio")
option.add_argument("user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1")

# Function to convert audio to text
def audioToText(mp3Path, driver):
    print("Switching to new tab...")
    driver.execute_script('''window.open("","_blank");''')
    driver.switch_to.window(driver.window_handles[1])
    print("Opening IBM Speech to Text page...")
    driver.get(googleIBMLink)
    time.sleep(2)

    print("Uploading audio file...")
    upload_input = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
    upload_input.send_keys(mp3Path)
    time.sleep(audioToTextDelay)

    print("Getting text from audio...")
    text_elements = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div[7]/div/div/div/span')
    result = " ".join([element.text for element in text_elements])

    print("Closing current tab...")
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return result

# Function to save file
def saveFile(response, filename):
    with open(filename, "wb") as handle:
        for data in response.iter_content():
            handle.write(data)

# Main script
driver = webdriver.Chrome(ChromeDriverManager().install(), options=option)
driver.get(byPassUrl)
time.sleep(2)

# Find and interact with the reCAPTCHA
googleClass = driver.find_elements_by_class_name('g-recaptcha')[0]
outeriframe = googleClass.find_element_by_tag_name('iframe')
outeriframe.click()
time.sleep(2)

# Find audio challenge iframe
allIframesLen = driver.find_elements_by_tag_name('iframe')
audioBtnFound = False
audioBtnIndex = -1

for index in range(len(allIframesLen)):
    driver.switch_to.default_content()
    iframe = driver.find_elements_by_tag_name('iframe')[index]
    driver.switch_to.frame(iframe)
    driver.implicitly_wait(delayTime)
    try:
        audioBtn = driver.find_element_by_id('recaptcha-audio-button') or driver.find_element_by_id('recaptcha-anchor')
        audioBtn.click()
        audioBtnFound = True
        audioBtnIndex = index
        break
    except Exception as e:
        pass

if audioBtnFound:
    try:
        while True:
            href = driver.find_element_by_id('audio-source').get_attribute('src')
            response = requests.get(href, stream=True)
            saveFile(response, filename)
            audio_text = audioToText(os.path.abspath(filename), driver)

            # Switch back to the challenge iframe
            driver.switch_to.default_content()
            iframe = driver.find_elements_by_tag_name('iframe')[audioBtnIndex]
            driver.switch_to.frame(iframe)
            
            input_btn = driver.find_element_by_id('audio-response')
            input_btn.send_keys(audio_text)
            input_btn.send_keys(Keys.ENTER)
            time.sleep(2)

            # Check if successful
            error_msg = driver.find_elements_by_class_name('rc-audiochallenge-error-message')[0]
            if error_msg.text == "" or error_msg.value_of_css_property('display') == 'none':
                print("Success")
                break

    except Exception as e:
        print(e)
        print('Error occurred. Need to change approach.')
else:
    print('Button not found. This should not happen.')

driver.quit()
