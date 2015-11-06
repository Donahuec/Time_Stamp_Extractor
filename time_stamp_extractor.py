"""
time_stamp_extractor.py 
By Caitlin Donahue 
caitlindonahue95@gmail.com 
summer 2015

Program made for searching through a specific field of a csv file, pulling out times in various formats, and putting them in a new sv file
This program looks at the data in the fourth column of the csv file
"""

import os
import sys
import csv
import re

class TimeStampExtractor:
    def __init__(self, extractionFile, saveFile):
        self.regex = []
        self.extractionFile = extractionFile
        self.saveFilePath = saveFile
        self.matches = []
        self.fileData = []
        self.updatedData = []
        self.needsWork = []

    def run(self):
        self.setUpRegex()
        self.extractData()
        for row in self.fileData:
            newRow, updated = self.searchForMatches(row)
            if updated:
                self.updatedData.append(newRow)
            else: 
                self.needsWork.append(newRow)
        self.writeCSV("nw", "TwoOrMoreTimeStamps")
        self.writeCSV("ud", "OneOrLessTimeStamp")
        print "----------------------"
        print "Time stamps extracted"
        print "----------------------"


    def setUpRegex(self):
        """ Sets up the regex objects needed to search for the time stamps """
        a = re.compile(r"([0-9]{0,2}(:|;))?[0-9]{0,2}:[0-9][0-9]")
        b = re.compile(r"[0-9]*[/]?[0-9]+ *(hr|h|hour|hours) *~?[0-9]*[/]?[0-9]+ *(min|m|minute|minutes);?\b")
        c = re.compile(r"\b[^a-b]?[0-9]*[/]?[0-9]+ *(hr|h);?\b")
        d = re.compile(r"\b[^a-b]?[0-9]*[/]?[0-9]+ *(min|m);?\b")
        e = re.compile(r"[0-9]*[/]?[0-9]+ *(hr|h|hour|hours)[0-9]*[/]?[0-9]+;?\b")
        self.regex.append(a)
        self.regex.append(b)
        self.regex.append(c)
        self.regex.append(d)
        self.regex.append(e)

    def extractData(self):
        """ Gets the data from a csv file and places it in a list of lists"""
        with open(self.extractionFile, "rb") as ef:
            dataReader = csv.reader(ef, delimiter=',' , quotechar='"')
            for row in dataReader:
                self.fileData.append(row)

    def searchForMatches(self, row):
        """ checks the 4th item in a list for matches to regex strings of times in different formats
        this returns a list with the time information inserted in a new column in the fourth position """
        data = row[3]
        allMatches = []
        aMatches = []
        bMatches = []
        cMatches = []
        dMatches = []
        eMatches = []
        timeStamp = ""
        #Find the matches for each type of string
        for match in self.regex[0].finditer(data):
            aMatches.append(match.group()) 
        for match in self.regex[1].finditer(data):
            bMatches.append(match.group())  
        for match in self.regex[2].finditer(data):
            cMatches.append(match.group())  
        for match in self.regex[3].finditer(data):
            dMatches.append(match.group())
        for match in self.regex[4].finditer(data):
            eMatches.append(match.group())      
        #now check to make sure there are no repeats that have been split up
        for match in aMatches:
            allMatches.append(match)
        for match in bMatches:
            allMatches.append(match)
        for match in eMatches:
            test = match + "m"
            testTwo = match + "min"
            if (test not in allMatches) and (testTwo not in allMatches):
                allMatches.append(match)
        for match in cMatches:
            succeeds = True
            for m in allMatches:
                for n in self.regex[2].finditer(m):
                    succeeds = False
            if succeeds:
                allMatches.append(match)

        for match in dMatches:
            succeeds = True
            for m in allMatches:
                for n in self.regex[3].finditer(m):
                    succeeds = False
            if succeeds:
                allMatches.append(match)
        for i in range(len(allMatches)):
            allMatches[i] = self.normalizeTimeFormat(allMatches[i])

        allMatches = self.stripIdenticals(allMatches)
        greatest = self.getGreatestDifference(allMatches)
        least = self.getLeastDifference(allMatches)
        lessThanMinute = "No"
        if greatest == "--------":
            lessThanMinute = "---"
        else:
            glist = greatest.split(":")
            for i in range(3):
                glist[i] = int(glist[i])
            if glist[0] == 0 and glist[1] == 0 and glist[2] < 20:
                lessThanMinute = "Yes"
        
        lgLessThanMin = "No"
        if greatest == "--------" or least == greatest:
            lgLessThanMin = "---"
        else:
            sub = self.timeSubtractor(least, greatest)
            subList = sub.split(":")
            for i in range(3):
                subList[i] = int(subList[i])
            if subList[0] == 0 and subList[1] == 0 and subList[2] < 20:
                lgLessThanMin = "Yes"

        if len(allMatches) == 2 and lessThanMinute == "Yes":
            comp = self.timeCompare(allMatches[0], allMatches[1])
            temp = []
            if comp == 1:
                temp.append(allMatches[0])
                allMatches = temp
            if comp == 2:
                temp.append(allMatches[1])
                allMatches = temp
        i = 0
        for match in allMatches:
            if i == 0:
                timeStamp = match
            else:
                timeStamp = timeStamp + "||" + match
            i += 1
        row.insert(3, timeStamp)
        row.insert(4,len(allMatches))
        row.insert(4, "< 20 sec diff: " + lessThanMinute)
        row.insert(4, "All close: " + lgLessThanMin)
        row.insert(4, "Greatest Diff: " + greatest)
        row.insert(4, "Least Diff: " + least)
        complete = False
        if len(allMatches) < 2:
            complete = True
        return row, complete

    def same(self, least):
        same = "No"
        if least == "--------":
            same = "---"
        elif least == "00:00:00":
            same = "Yes"
        return same

    def stripIdenticals(self, matches):
        newList = []
        for i in matches:
            if i not in newList:
                newList.append(i)
        return newList

    def getGreatestDifference(self, matches):
        curBest = "00:00:00"
        if len(matches) <= 1:
            return "--------"
        for i in range(len(matches)):
            for k in range(len(matches)):
                if k > i:
                    dif = self.timeSubtractor(matches[i],matches[k])
                    comp = self.timeCompare(dif, curBest)
                    if comp == 1:
                        curBest = dif
        return curBest

    def getLeastDifference(self, matches):
        curBest = "99:99:99"
        if len(matches) <= 1:
            return "--------"
        for i in range(len(matches)):
            for k in range(len(matches)):
                if k > i:
                    dif = self.timeSubtractor(matches[i],matches[k])
                    comp = self.timeCompare(dif, curBest)
                    if comp == 2:
                        curBest = dif
        if curBest == "99:99:99":
            curBest = "--------"
        return curBest

    def normalizeTimeFormat(self,time):
        desiredFormat = re.compile(r"[0-9][0-9]:[0-9][0-9]:[0-9][0-9]")
        if desiredFormat.match(time):
            return time
        charsToStrip = re.compile(r"[~ inr]")
        for match in charsToStrip.finditer(time):
            time = time.replace(match.group(), "")
        if re.match(r"\b[0-9]:[0-9][0-9]:[0-9][0-9]", time):
            time = "0" + time
        elif re.match(r"\b[0-9]{1,2}:[0-9]{1,2}\b" , time):
            if re.match(r"0[0-9]:", time):
                time = time + ":00"
            elif re.match(r"[0-9]:", time):
                m = re.match(r"[0-9]", time)
                temp = int(m.group())
                if temp < 2:
                    time = "0" + time + ":00"
                else:
                    time = "00:" + time
            elif re.match(r"[1-9][0-9]:", time):
                time = "00:" + time
        elif re.match(r"\b[0-9]:[0-9][0-9]:[0-9]", time):
            time = "0" + time
        elif re.match(r"\b:[0-9][0-9]$", time):
            time = "00:00:" + time
        elif re.match(r"[0-9]*h?[0-9]*m?$", time):
            hour = re.search(r"[0-9]*h", time)
            minute = re.search(r"[0-9]+m?$", time)
            temp = ""
            if hour:
                hours = hour.group()
                hours = hours.replace("h","")
                if not re.match(r"[0-9][0-9]$",hours):
                    hours = "0" + hours
                temp = temp + hours + ":"
            else:
                temp = "00:"
            if minute:
                minutes = minute.group()
                minutes = minutes.replace("m", "")
                if not re.match(r"[0-9][0-9]$", minutes):
                    minutes  = "0" + minutes
                temp = temp + minutes + ":00"
                time = temp
            else:
                temp = temp + "00:00"
            time = temp
        else:
            time = time + "<Unknown>"
        time_list = time.split(":")
        for i in range(3):
            time_list[i] = int(time_list[i])
        if time_list[2] >= 60:
            div = time_list[2] / 60
            mod = time_list[2] % 60
            time_list[1] = time_list[1] + div
            time_list[2] = mod
        if time_list[1] >= 60:
            div = time_list[1] / 60
            mod = time_list[1] % 60
            time_list[0] = time_list[0] + div
            time_list[1] = mod
        for i in range(3):
            time_list[i] = "{:0>2d}".format(time_list[i])
        time = time_list[0] + ":" + time_list[1] + ":" + time_list[2]
        return time

    def timeCompare(self, timeOne,timeTwo):
        a = timeOne.split(":")
        b = timeTwo.split(":")
        for i in range(3):
            a[i] = int(a[i])
            b[i] = int(b[i])
        if a[0] > b[0]:
            return 1
        elif b[0] > a[0]:
            return 2
        else:
            if a[1] > b[1]:
                return 1
            elif b[1] > a[1]:
                return 2
            else:
                if a[2] > b[2]:
                    return 1
                elif b[2] > a[2]:
                    return 2
                else:
                    return 0

    def timeSubtractor(self, timeOne, timeTwo):
        compare = self.timeCompare(timeOne, timeTwo)
        if compare == 1:
            a = timeOne.split(":")
            b = timeTwo.split(":")
        elif compare == 2:
            b = timeOne.split(":")
            a = timeTwo.split(":")
        else:
            return "00:00:00"            
        for i in range(3):
            a[i] = int(a[i])
            b[i] = int(b[i])
        outcome = [0,0,0]
        seconds = a[2] - b[2]
        if seconds >= 0:
            outcome[2] = seconds
        else:
            a[1] -= 1
            seconds = 60 - b[2] + a[2]
            outcome[2] = seconds
        minutes = a[1] - b[1]
        if minutes >= 0:
            outcome[1] = minutes
        else:
            a[0] -= 1
            minutes = 60 - b[1] + a[1]
            outcome[1] = minutes
        outcome[0] = a[0] - b[0]
        for i in range(3):
            outcome[i] = "{:0>2d}".format(outcome[i])
        dif = outcome[0] + ":" + outcome[1] + ":" + outcome[2]
        return dif

    def writeCSV(self, data, suffix):
        """ Writes the data with the extracted time stamps to a new csv file"""
        toUse = []
        if data == "nw":
            toUse = self.needsWork
        elif data == "ud":
            toUse = self.updatedData
        temp = os.path.basename(self.extractionFile).replace(".csv", "") 
        outFile = os.path.join( self.saveFilePath, temp + suffix + ".csv")
        with open(outFile, "wb") as f:
            writer = csv.writer(f, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
            for row in toUse:
                writer.writerow(row)

def main():
    extractionFile = sys.argv[1]
    saveLocation = sys.argv[2]
    extractor = TimeStampExtractor(extractionFile, saveLocation)
    extractor.run()
main()









