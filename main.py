import os
import re
import sys
import base64
import random

from typing import Optional, Union

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.webdriver.common.by import By


def get_file_content_chrome(driver, uri):
    result = driver.execute_async_script("""
    var uri = arguments[0];
    var callback = arguments[1];
    var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
    var xhr = new XMLHttpRequest();
    xhr.responseType = 'arraybuffer';
    xhr.onload = function(){ callback(toBase64(xhr.response)) };
    xhr.onerror = function(){ callback(xhr.status) };
    xhr.open('GET', uri);
    xhr.send();
    """, uri)
    if type(result) == int:
        raise Exception("Request failed with status %s" % result)
    return base64.b64decode(result)


def create_webdriver(options: Optional[Union[list, str]] = None) -> ChromeWebDriver:
    chrome_options = ChromeOptions()
    if options is not None:
        if isinstance(options, str):
            chrome_options.add_argument(options)
        elif isinstance(options, list):
            [chrome_options.add_argument(option) for option in options]
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def main() -> int:
    target_site = 'https://voicechanger.io/'
    driver = create_webdriver(["--headless", "--mute-audio"])
    driver.get(target_site)
    voices = []
    voice_effects = driver.find_elements(By.XPATH, "/html/body/section[4]/div/*")
    for element in voice_effects:
        if element.tag_name == 'div':
            try:
                title_element = element.find_element(By.TAG_NAME, "h2")
                title = title_element.get_attribute("textContent")
                if title == "":
                    pattern = r"loadTransform\(event, '(.+?)'\)"
                    match = re.search(pattern, element.get_attribute("onclick"))
                    if match:
                        result = match.group(1)
                        title = result.capitalize()
                voice_card = element
                voice_data = {
                    "title": title,
                    "voice_card": voice_card
                }
                voices.append(voice_data)
            except NoSuchElementException:
                pass
    file_input = driver.find_element(By.XPATH, "/html/body/section[3]/div[1]/div[1]/input")
    file_input.send_keys(os.path.abspath("sample.mp3"))
    audio_load_card = driver.find_element(By.XPATH, "//*[@id=\"audio-load-success\"]")
    audio_load_card_display = audio_load_card.value_of_css_property("display")
    while audio_load_card_display == 'none':
        audio_load_card_display = audio_load_card.value_of_css_property("display")
    voice_card = (random.choice(voices))["voice_card"]
    voice_card.click()
    audio_element = driver.find_element(By.XPATH, "//*[@id=\"output-audio-tag\"]")
    audio_src = audio_element.get_attribute("src")
    while audio_src is None or audio_src == "":
        audio_src = audio_element.get_attribute("src")
    audio_bytes = get_file_content_chrome(driver, audio_src)
    file_path = os.path.abspath("edited_sample.mp3")
    with open(file_path, "wb") as file:
        file.write(audio_bytes)
    return 0


if __name__ == "__main__":
    sys.exit(main())
