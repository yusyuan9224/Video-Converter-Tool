import os
import locale
import configparser
from tkinter import filedialog, Tk
from moviepy.editor import VideoFileClip, AudioFileClip
from concurrent.futures import ThreadPoolExecutor
import subprocess
import time

class ConverterApp:
    def __init__(self):
        self.num_files = 0
        self.output_dir = ""
        self.hw_accel = False
        self.system_message = ""
        self.language = self.detect_system_language()
        self.translations = self.load_translations()


        print(self.translations['loading'])
        time.sleep(2)  

    def detect_system_language(self):
        # Detect the system language
        system_lang = locale.getdefaultlocale()[0]
        if system_lang.startswith('en'):
            return 'en'
        elif system_lang.startswith('zh'):
            return 'zh'
        elif system_lang.startswith('ja'):
            return 'ja'
        elif system_lang.startswith('es'):
            return 'es'
        else:
            return 'en'  # Default to English if the system language is not supported

    def load_translations(self):
        # Load translations based on the system language
        config = configparser.ConfigParser()
        config.read('languages.ini', encoding='utf-8')
        return config[self.language]

    def display_menu(self):
        # Display the menu options
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self.translations['menu_system_message'])
        print(self.system_message)
        print(f"\n{self.translations['menu_title']}")
        print(self.translations['menu_option_1'])
        print(self.translations['menu_option_2'])
        print(self.translations['menu_option_3'])
        print(self.translations['menu_option_4'])
        print(self.translations['menu_option_5'])
        print()

    def menu(self):
        # Main menu loop
        while True:
            self.display_menu()
            choice = input()
            if choice == "1":
                self.select_files()
            elif choice == "2":
                self.select_output_dir()
            elif choice == "3":
                self.check_hardware_acceleration()
            elif choice == "4":
                if self.num_files > 0:
                    self.start_conversion()
                else:
                    self.system_message = self.translations['prompt_no_files_selected']
            elif choice == "5":
                print(self.translations['exit'])
                break
            else:
                self.system_message = self.translations['prompt_invalid_choice']

    def select_files(self):
        # Select files to convert
        root = Tk()
        root.withdraw()
        root.update()

        file_paths = filedialog.askopenfilenames(title=self.translations['menu_option_1'], filetypes=[("所有檔案", "*.*")])
        
        if file_paths:
            self.file_paths = file_paths
            self.num_files = len(file_paths)
            self.system_message = f"{self.num_files} files selected."
        else:
            self.system_message = self.translations['prompt_no_files_selected']

    def select_output_dir(self):
        # Select output directory
        root = Tk()
        root.withdraw()
        root.update()

        output_dir = filedialog.askdirectory(title=self.translations['menu_option_2'])
        if output_dir:
            self.output_dir = output_dir
            self.system_message = f"Output directory set to: {self.output_dir}"
        else:
            self.system_message = "Using original file location."

    def check_hardware_acceleration(self):
        # Check if hardware acceleration is supported
        self.hw_accel = self.detect_hardware_acceleration()
        support = 'Yes' if self.hw_accel else 'No'
        self.system_message = self.translations['prompt_hw_acceleration_support'].format(support=support)

    def start_conversion(self):
        # Start the conversion process
        try:
            with ThreadPoolExecutor() as executor:
                futures = []
                for file_path in self.file_paths:
                    futures.append(executor.submit(self.convert_single_file_to_mp4, file_path))

                for i, future in enumerate(futures):
                    future.result()
                    self.system_message = f"{self.translations['prompt_conversion_progress']} {(i + 1) / self.num_files * 100:.2f}%"
                    self.display_menu()

            self.system_message = self.translations['prompt_conversion_complete']
        except Exception as e:
            self.system_message = f"Error occurred during conversion: {e}"

    def convert_single_file_to_mp4(self, file_path):
        # Convert a single file to MP4 format
        try:
            new_file_name = input(self.translations['prompt_enter_filename'].format(filename=os.path.basename(file_path).split('.')[0]))
            if not new_file_name:
                new_file_name = os.path.basename(file_path).split('.')[0] + "_converted"
            
            if self.output_dir:
                output_path = os.path.join(self.output_dir, new_file_name + ".mp4")
            else:
                output_path = os.path.join(os.path.dirname(file_path), new_file_name + ".mp4")

            if file_path.endswith(('.wav', '.mp3')):
                clip = AudioFileClip(file_path)
                clip.write_videofile(output_path, codec="libx264", fps=24, preset="fast", threads=4)
            else:
                clip = VideoFileClip(file_path)
                if self.hw_accel:
                    clip.write_videofile(output_path, codec="h264_nvenc", threads=4)
                else:
                    clip.write_videofile(output_path, codec="libx264", preset="fast", threads=4)
            
            clip.close()
            self.system_message = f"{file_path} conversion successful, saved to {output_path}"
        except Exception as e:
            self.system_message = f"Error converting {file_path}: {e}"

    def detect_hardware_acceleration(self):
        # Detect if hardware acceleration is available
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-hwaccels"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return 'cuda' in result.stdout or 'nvenc' in result.stdout
        except Exception as e:
            return False

if __name__ == "__main__":
    app = ConverterApp()
    app.menu()
