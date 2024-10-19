import tkinter as tk
from tkinter import font as tkFont
import google.generativeai as genai
import base64
import tempfile
import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import dotenv

dotenv.load_dotenv()

class MathNotes():
    def __init__(self, root):
        self.root = root
        self.root.title("Math Notes - AI")

        self.canvas_width = 1000
        self.canvas_height = 600

        self.canvas = tk.Canvas(root, bg='black', width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        self.root.bind("<Command-Z>", self.command_undo)
        self.root.bind("<Return>", self.command_calculate)

        self.current_action = []
        self.actions = []
        self.last_x = None
        self.last_y = None

        self.button_clear = tk.Button(root, text="Clear", command=self.clear)
        self.button_clear.pack(side=tk.LEFT)

        self.button_undo = tk.Button(root, text="Undo", command=self.undo)
        self.button_undo.pack(side=tk.LEFT)

        self.button_calculate = tk.Button(root, text="Calculate", command=self.calculate)
        self.button_calculate.pack(side=tk.LEFT)

        self.font = ImageFont.truetype("arial.ttf", 40) 

        genai.configure(api_key=os.getenv("GENAI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def start_drawing(self, event):
        self.current_action = []
        self.last_x, self.last_y = event.x, event.y

    def paint(self, event):
        x, y = event.x, event.y
        if self.last_x and self.last_y:
            line_id = self.canvas.create_line((self.last_x, self.last_y, x, y), fill='white', width=5)
            self.draw.line((self.last_x, self.last_y, x, y), fill='white', width=5)
            self.current_action.append((line_id, (self.last_x, self.last_y, x, y)))
        self.last_x, self.last_y = x, y

    def reset(self, event):
        self.last_x, self.last_y = None, None
        if self.current_action:
            self.actions.append(self.current_action)

    def clear(self):
        self.canvas.delete('all')
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.actions = []

    def undo(self):
        if self.actions:
            last_action = self.actions.pop()
            for line_id, coords in last_action:
                self.canvas.delete(line_id)
            self.redraw_all()

    def redraw_all(self):
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.delete('all')
        for action in self.actions:
            for _, coords in action:
                self.draw.line(coords, fill='white', width=5)
                self.canvas.create_line(coords, fill='white', width=5)

    def draw_answer(self, answer):
        if not self.actions:
            return
        
        last_action = self.actions[-1]
        last_coords = last_action[-1][-1]

        equals_x = last_coords[2]
        equals_y = last_coords[3]

        x_start = equals_x + 70
        y_start = equals_y - 20

        self.canvas.create_text(x_start, y_start, text=answer, font=("Arial", 40), fill='#11ff00')

        self.draw.text((x_start, y_start - 50), answer, font=self.font, fill='#11ff00')

    def calculate(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            temp_filename = temp_file.name
            self.image.save(temp_filename, format='PNG')

        try:
            self.image = ImageEnhance.Contrast(self.image).enhance(2.0)
            self.image.save(temp_filename, format='PNG')

            # Upload and send to the AI model
            uploaded_file = genai.upload_file(temp_filename)
            prompt = (
                "Identify and calculate the mathematical expression in the image. "
                "Only return the answer in numbers. Do not respond with words. "
                "Look for an equation with an equal sign but no number after it."
            )
            result = self.model.generate_content([uploaded_file, prompt])
            answer = result.text.strip()

            self.draw_answer(answer)

        except Exception as e:
            print(f"Error during AI calculation: {e}")
        finally:
            os.unlink(temp_filename)  

    def command_undo(self, event):
        self.undo()

    def command_calculate(self, event):
        self.calculate()

if __name__ == "__main__":
    root = tk.Tk()
    app = MathNotes(root)
    root.mainloop()
