#!/usr/bin/env python3
import sys
import time
import argparse

from PIL import Image, ImageOps, ImageDraw, ImageFont

# <<< ADATTA QUI IL PERCORSO DELLA LIBRERIA WAVESHARE >>>
sys.path.insert(0, './epaper-python-library/lib')

from waveshare_epd import epd4in2_V2

EPD = epd4in2_V2.EPD  # se serve, cambia in epd4in2.EPD


# ======================
#  IMMAGINI
# ======================

def load_image_for_epaper(path, size=(400, 300), dither=True, rotate=0):
	img = Image.open(path).convert("L")
	img = ImageOps.exif_transpose(img)
	if rotate:
		img = img.rotate(rotate, expand=True)

	tw, th = size
	img.thumbnail((tw, th), Image.LANCZOS)
	canvas = Image.new("L", size, 255)
	x = (tw - img.width) // 2
	y = (th - img.height) // 2
	canvas.paste(img, (x, y))

	if dither:
		return canvas.convert("1")  # dithering
	else:
		return canvas.point(lambda p: 255 if p > 128 else 0, mode="1")


def show_fullscreen_image(epd, path, dither=True, rotate=0):
	img1b = load_image_for_epaper(
		path,
		size=(epd.width, epd.height),
		dither=dither,
		rotate=rotate
	)
	epd.display(epd.getbuffer(img1b))


# ======================
#  TESTO INTERATTIVO
# ======================

def create_text_image(lines, width, height, margin_x=10, margin_y=10, line_spacing=20):
	"""
	Crea una immagine 1-bit (bianco/nero) con le righe di testo fornite.
	lines: lista di stringhe
	"""
	# 1-bit: 0 = nero, 1 = bianco
	img = Image.new("1", (width, height), 1)
	draw = ImageDraw.Draw(img)

	# Font base (quello di default va benissimo)
	font = ImageFont.load_default()
	y = margin_y

	for line in lines:
		draw.text((margin_x, y), line, font=font, fill=0)
		y += line_spacing
		if y > height - line_spacing:
			break

	return img


def interactive_text_mode(epd):
	"""
	Modalità: leggi righe dal terminale e mostrale sul display.
	Riga vuota = esci.
	"""
	lines = []
	# stimo quante righe stanno sul display
	font = ImageFont.load_default()
	line_height = font.getbbox("Hg")[3]  # altezza approssimata
	line_spacing = line_height + 4
	max_lines = (epd.height - 20) // line_spacing

	print("Modalità testo interattivo.")
	print("Scrivi e premi Invio per aggiornare il display.")
	print("Riga vuota per uscire.\n")

	while True:
		try:
			s = input("> ")
		except EOFError:
			break

		if s.strip() == "":
			print("Uscita.")
			break

		lines.append(s)
		if len(lines) > max_lines:
			lines = lines[-max_lines:]

		img = create_text_image(
			lines,
			width=epd.width,
			height=epd.height,
			margin_x=10,
			margin_y=10,
			line_spacing=line_spacing
		)
		epd.display(epd.getbuffer(img))
		time.sleep(0.1)


# ======================
#  MAIN
# ======================

def main():
	parser = argparse.ArgumentParser(
		description="WeAct / Waveshare 4.2\" e-paper: testo interattivo o immagine."
	)
	parser.add_argument(
		"--image",
		help="Percorso immagine da mostrare fullscreen (modalità immagine)."
	)
	parser.add_argument(
		"--nodither",
		action="store_true",
		help="Disabilita dithering (soglia secca)."
	)
	parser.add_argument(
		"--rotate",
		type=int,
		default=0,
		help="Rotazione immagine in gradi (0, 90, 180, 270)."
	)

	args = parser.parse_args()

	epd = EPD()
	epd.init()

	try:
		if args.image:
			# Modalità immagine, come nel tuo script
			show_fullscreen_image(
				epd,
				args.image,
				dither=not args.nodither,
				rotate=args.rotate
			)
		else:
			# Modalità testo interattiva
			interactive_text_mode(epd)

	finally:
		print("Sleep e-paper.")
		epd.sleep()


if __name__ == "__main__":
	main()
