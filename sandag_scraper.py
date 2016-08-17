import os, sys
from bs4 import BeautifulSoup
import requests
import urllib
import PyPDF2


committies = {"borders": ["http://www.sandag.org/index.asp?committeeid=54&fuseaction=committees.detail#mSched", PyPDF2.PdfFileWriter()], 
"executive": ["http://www.sandag.org/index.asp?committeeid=15&fuseaction=committees.detail#mSched", PyPDF2.PdfFileWriter()], 
"public safety": ["http://www.sandag.org/index.asp?committeeid=66&fuseaction=committees.detail#mSched", PyPDF2.PdfFileWriter()], 
"regional planning": ["http://www.sandag.org/index.asp?committeeid=49&fuseaction=committees.detail#mSched", PyPDF2.PdfFileWriter()], 
"transportation": ["http://www.sandag.org/index.asp?committeeid=28&fuseaction=committees.detail#mSched", PyPDF2.PdfFileWriter()]
}

sections = {"agendas":"Agenda", "minutes":"Minutes", 
"board actions":"Board Actions", 
"voting results":"Voting Results"
}

bdir = "/sandag scraping" #the folder that contains the folders where all the pdfs will be downloaded to

#gets the links that contain data from years 2002 - 2016
def getYears(c):
	#get all elements with class "body header" -- the one with the years is the last one
	link = committies[c][0]
	r = requests.Session().get(link, allow_redirects=False)
	soup = BeautifulSoup(r.content, "lxml")
	pTags = soup.find_all("p", class_="bodyheader") 
	yearLinks = []
	index = -1 # index of last tag with class "bodyheader"
	if (c == "public safety"):
		index = -2
	aTags = pTags[index].find_all("a")
	base = "http://www.sandag.org"
	for a in aTags:
		yearLinks.append(base + a["href"])
	return yearLinks

#downloads pdf & returns directory it was downloaded to 
def downloadAsPdf(t, baseWeb, baseDir):
	pdfLink = baseWeb + t["href"]
	downloadFilename = pdfLink.split("/")[-1]
	directory = baseDir + "/pdf/" + downloadFilename
	txtDir = baseDir + "/text/" + downloadFilename + ".txt"
	try:
		urllib.request.urlretrieve(pdfLink, directory )
	except:
		print("couldn't download pdf", pdfLink)
	return [directory, txtDir]

# some of this from http://code.activestate.com/recipes/511465-pure-python-pdf-to-text-converter/
def getPDFContent(path, tfile):
	e = 0
	try:
		pdf = PyPDF2.PdfFileReader(open(path, "rb"))
	except:
		print("couldn't open", path)
		return

	for i in range(0, pdf.getNumPages()):
		for line in pdf.getPage(i).extractText().splitlines():
			
			try:
				tfile.write( str(line.encode("utf_8", "xmlcharrefreplace"), "utf_8")  + "\n") 
			except:
				e += 1
				print(path, e)
	
#downloads pdf as txt file
def downloadAsTxt(info):
	pdf = info[0]
	txt = info[1]
	tfile = open(txt, 'w') # info[1] is the txt directory
	if (pdf.split(".")[-1] == "pdf"):
		print("writing line")
		getPDFContent(pdf, tfile) # info[0] is the directory where the pdf file is already downloaded

#adds pages to pdf that contains all tables for a committie
def addToTablePdf(c,filename):
	try:
		pdf = PyPDF2.PdfFileReader(open(filename, "rb"))
	except:
		print("couldn't open", filename)
		return
	output = committies[c][1]
	startTable = -1
	for i in range(0, pdf.getNumPages()):
		txt = pdf.getPage(i).extractText()
		etxt = str(txt.encode("utf_8", "xmlcharrefreplace"), "utf_8")
		if ("CONFIRMED ATTENDANCE" and "JURISDICTION" and "NAME") in etxt: #first pages of every table have these
			startTable = i
			break
		if (startTable != -1):
			for j in range(startTable, pdf.getNumPages()):
				txt = pdf.getPage(j).extractText()
				etxt = str(txt.encode("utf_8", "xmlcharrefreplace"), "utf_8")
				if ("Member" or "Alternate") in etxt: #every table page has these
					output.addPage(pdf.getPage(j))

#downloads pdf, if minutes downloads as txt and adds it to the pdf of all tables for that committie
def downloadPdfNtxt(c, s, soup):
	baseDir = bdir + "/" + c + "/" + s
	baseWeb = "http://www.sandag.org"
	innertxt = sections[s]
	sectionTags = soup.find_all("a", text = innertxt)
	for t in sectionTags:
		info = downloadAsPdf(t, baseWeb, baseDir)
		if (s == "minutes"):
			#downloadAsTxt(info)
			pdf = info[0]
			addToTablePdf(c,pdf)


#posts request to pdftables.com to make a csv out of the pdf of tables
def makeCsv(c, filename):
	output = committies[c][1]
	filename = "allTables%s.pdf" %c
	with open(filename, "wb") as outputStream:
		output.write(outputStream)
	files = {} #dict to pass to the pdftables site
	files["f"] = (filename, open(filename, "rb"))
	apiKey = "61s6o6btaxsy" #create an account on the website & replace with your own api key
	response = requests.post("https://pdftables.com/api?key=%s&format=csv" %apiKey, files=files) 
	response.raise_for_status() # ensure we notice bad responses
	with open("allData%s.csv" %c, "wb") as f:
		f.write(response.content)


#this function is a combination of a bunch of the above functions, not really needed
#use if you've already downloaded all the pdfs, but had issues with putting them into one pdf or downloading as csv
def getTablesFromDownloadedPdfs():
	for c in committies.keys():
		directory = bdir + "/" + c + "/minutes/pdf/"
		allPdfs = os.listdir(directory)
		output = PyPDF2.PdfFileWriter()
		for p in allPdfs:
			startTable = -1
			path = directory + p
			pdf = PyPDF2.PdfFileReader(open(path, "rb"))
			for i in range(0, pdf.getNumPages()):
				txt = pdf.getPage(i).extractText()
				etxt = str(txt.encode("utf_8", "xmlcharrefreplace"), "utf_8")
				if ("CONFIRMED ATTENDANCE" and "JURISDICTION" and "NAME") in etxt:
					startTable = i
					break
			if (startTable != -1):
				for j in range(startTable, pdf.getNumPages()):
					txt = pdf.getPage(j).extractText()
					etxt = str(txt.encode("utf_8", "xmlcharrefreplace"), "utf_8")
					if ("Member" or "Alternate") in etxt:
						output.addPage(pdf.getPage(j))
		filename = bdir + "/scraping_files/allTables%s.pdf" %c
		with open(filename, "wb") as outputStream:
			output.write(outputStream)
		makeCsv(c, filename)

#main method
def scrape():
	for c in committies.keys():
		years = getYears(c)
		for y in years:
			r = requests.Session().get(y) 
			soup = BeautifulSoup(r.content, "lxml")
			for s in sections.keys(): 
				downloadPdfNtxt(c, s, soup)
		makeCsv(c)

scrape()







