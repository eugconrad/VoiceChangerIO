
import os
import re
import base64

from contextlib import suppress
from typing import Optional, Union, List, cast, Literal, Final

from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.webdriver import WebDriver as ChromeWebDriver
from selenium.common.exceptions import NoSuchElementException

from .errors import BadRequest
from .models import VoiceEffect


BASE_URL: Final[str] = "https://voicechanger.io/"


class SingletonMeta(type):
    """
    Metaclass for implementing the Singleton pattern.

    This metaclass ensures that only one instance of a class is created and
    provides a global point of access to that instance.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Call method that controls the creation of class instances.

        This method is called when a class instance is created using the class
        name as a callable. It ensures that only one instance of the class is
        created and returned.

        Args:
            cls (type): The class object.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            object: The instance of the class.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


class VoiceChangerIO(metaclass=SingletonMeta):
    """
    Class for interacting with the VoiceChangerIO website.

    This class provides an interface to the voice transformation functionality
    of the VoiceChanger.io website. It allows you to apply various voice effects
    to audio files programmatically using a web browser automation approach.
    """
    driver: ChromeWebDriver
    voice_effects: List[VoiceEffect]

    def __init__(self, *driver_options: str) -> None:
        """
        Initializes the VoiceChangerIO instance.

        Args:
            *driver_options: Variable length arguments representing the driver options.
        """
        self.driver = self.create_webdriver(*driver_options)
        self.reload()

    @staticmethod
    def create_webdriver(*options: str) -> ChromeWebDriver:
        """
        Creates a Chrome WebDriver instance with the specified options.

        Args:
            *options: Variable length arguments representing the driver options.

        Returns:
            The created Chrome WebDriver instance.
        """
        chrome_options = ChromeOptions()
        [chrome_options.add_argument(option) for option in options]
        return Chrome(options=chrome_options)

    def get_file_content_chrome(self, uri: str) -> bytes:
        """
        Retrieves the content of a file from a given URI using Chrome WebDriver.

        Args:
            uri: The URI of the file to retrieve.

        Returns:
            The content of the file as bytes.

        Raises:
            BadRequest: If the request to retrieve the file fails.
        """
        result = self.driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)  # noqa
        if isinstance(result, int):
            raise BadRequest("Request failed with status code {}", result)
        return base64.b64decode(result)

    def reload(self) -> Literal[True]:
        """
        Reloads the VoiceChangerIO instance by navigating to the base URL and updating the voice effects.

        Returns:
            Literal[True] to indicate a successful reload.
        """
        self.driver.get(BASE_URL)
        self.voice_effects = self.get_voice_effects()
        return True

    def get_voice_effects(self) -> List[VoiceEffect]:
        """
        Retrieves the list of available voice effects from the VoiceChangerIO website.

        Returns:
            The list of available voice effects as VoiceEffect objects.
        """
        voice_effects_element = self.driver.find_elements(By.XPATH, "/html/body/section[4]/div/*")
        voice_effects = []
        for i, element in enumerate(voice_effects_element):
            if element.tag_name == "div":
                with suppress(NoSuchElementException):
                    title_element = element.find_element(By.TAG_NAME, "h2")
                    title = title_element.get_attribute("textContent")
                    if not title:
                        pattern = r"loadTransform\(event, '(.+?)'\)"
                        match = re.search(pattern, element.get_attribute("onclick"))
                        if match:
                            result = match.group(1)
                            title = result.capitalize()
                    voice_effects.append(
                        VoiceEffect(id=i, title=title, element=element)
                    )
        return voice_effects

    def update_voice_effects(self) -> Literal[True]:
        """
        Updates the list of available voice effects by retrieving the latest data from the website.

        Returns:
            Literal[True] to indicate a successful update.
        """
        self.voice_effects = self.get_voice_effects()
        return True

    def find_voice_effect(
            self, voice_effect_id: Optional[int] = None, voice_effect_title: Optional[str] = None
    ) -> Optional[VoiceEffect]:
        """
        Finds a voice effect with the specified ID or title.

        Args:
            voice_effect_id: The ID of the voice effect to find.
            voice_effect_title: The title of the voice effect to find.

        Returns:
            The found VoiceEffect object, or None if no matching voice effect is found.
        """
        for voice_effect in self.voice_effects:
            if (voice_effect_id is not None and voice_effect.id == voice_effect_id) or (
                    voice_effect_title and voice_effect.title.lower() == voice_effect_title.lower()):
                return voice_effect
        return None

    def search_voice_effects(
            self, voice_effect_id: Optional[int] = None, voice_effect_title: Optional[str] = None
    ) -> List[VoiceEffect]:
        """
        Searches for voice effects based on the specified ID or title.

        Args:
            voice_effect_id: The ID of the voice effect to search for.
            voice_effect_title: The title of the voice effect to search for.

        Returns:
            The list of matching VoiceEffect objects.
        """
        result = []
        for voice_effect in self.voice_effects:
            if (voice_effect_id is not None and voice_effect.id == voice_effect_id) or (
                    voice_effect_title and voice_effect.title.lower() == voice_effect_title.lower()):
                result.append(voice_effect)
        return result

    def upload_audio(self, audio_file: Union[bytes, str]) -> Literal[True]:
        """
        Uploads an audio file to the VoiceChangerIO website.

        Args:
            audio_file: The audio file to upload, either as bytes or a file path.

        Returns:
            Literal[True] to indicate a successful upload.
        """
        file_input = self.driver.find_element(By.XPATH, "/html/body/section[3]/div[1]/div[1]/input")
        if isinstance(audio_file, bytes):
            audio_file = self.save_audio_file(audio_file)
        file_input.send_keys(audio_file)
        audio_load_card = self.driver.find_element(By.XPATH, "//*[@id=\"audio-load-success\"]")
        audio_load_card_display = audio_load_card.value_of_css_property("display")
        while audio_load_card_display == "none":
            audio_load_card_display = audio_load_card.value_of_css_property("display")
        return True

    def get_output_audio_src(self) -> str:
        """
        Retrieves the source URL of the output audio element on the VoiceChangerIO website.

        Returns:
            The source URL of the output audio.
        """
        audio_element = self.driver.find_element(By.XPATH, "//*[@id=\"output-audio-tag\"]")
        audio_src = audio_element.get_attribute("src")
        while audio_src is None or audio_src == "":
            audio_src = audio_element.get_attribute("src")
        return cast(str, audio_src)

    def download_output_audio(self, audio_src: str) -> bytes:
        """
        Downloads the output audio file from the specified source URL.

        Args:
            audio_src: The source URL of the output audio.

        Returns:
            The downloaded audio file as bytes.
        """
        audio_bytes = self.get_file_content_chrome(audio_src)
        return audio_bytes

    @staticmethod
    def save_audio_file(audio_file: bytes, custom_name: Optional[str] = None) -> str:
        """
        Saves an audio file to the local filesystem.

        Args:
            audio_file: The audio file as bytes.
            custom_name: Optional custom name for the saved file.

        Returns:
            The absolute path of the saved audio file.
        """
        if custom_name and not custom_name.lower().endswith(".mp3"):
            custom_name += ".mp3"
        file_path = os.path.abspath(custom_name or f".VoiceChangerIO.mp3")
        with open(file_path, "wb") as binary_file:
            binary_file.write(audio_file)
        return file_path

    def apply_voice_effect(self, audio_file: bytes, voice_effect: VoiceEffect) -> bytes:
        """
        Applies a voice effect to an audio file.

        Args:
            audio_file: The audio file as bytes.
            voice_effect: The VoiceEffect object representing the voice effect to apply.

        Returns:
            The modified audio file as bytes.
        """
        self.upload_audio(audio_file)
        voice_effect.element.click()
        audio_src = self.get_output_audio_src()
        audio_file = self.download_output_audio(audio_src)
        return audio_file

    def __str__(self) -> str:
        """
        Return a string representation of the VoiceChangerIO instance.

        The string includes information about the number of available voice effects.

        Returns:
            str: String representation of the VoiceChangerIO instance.
        """
        return f"VoiceChangerIO instance with {len(self.voice_effects)} voice effects"
