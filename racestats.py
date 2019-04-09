

import csv

# Cell numbers in CSV, remember to count from 0 not 1
RACE_CLASS = 1
SHELTER = 3
YEAR = 4
CAR_NO = 2
OWNER = 6
CAR_MODEL = 5
RACE_PRACTICE = 0
FIRST_DATA_CELL = 12
HTP_NO = 8
HTP_ISSUE = 9
HTP_EXPIRE = 9
NOTES = 37
WEIGHT_ACTUAL = 35
WEIGHT_HTP = 13
CHECKED = 12

DEBUG = True

# read csv and return list containing rows.
# Assumes that line 0 is the title line and that all lines should have as many
# cells as the title line
def readcsv(inputfilename):
    csvdata = []
    with open(inputfilename, 'rb') as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            if any(x.strip() for x in row):
                csvdata.append(row)
    title_len = len(csvdata[0])
    count = 1
    for row in csvdata:
        if len(row) != title_len:
            if DEBUG:
                print "WARNING: row %d has %d cells, expected %d" % (count, len(row), title_len)
        count += 1
    return csvdata

# break down csv data into races, by splitting on class/race number
def split_race(carlist):
  classdict = {}
  for row in carlist[1:]:
    # if the class isnt already in the dictionary, add it and add the car,
    # otherwise just add cars to that class
    if row[RACE_CLASS] not in classdict.keys():
      classdict[row[RACE_CLASS]] = []
      classdict[row[RACE_CLASS]].append(row)
    else:
      classdict[row[RACE_CLASS]].append(row)
  if DEBUG:
      print "DEBUG: Split %d rows into %d races:" % (len(carlist), len(classdict))
      for key in classdict.keys():
          print "- %s : %d" % (key, len(classdict[key]))
      print ""
  return classdict


# generate stats by 'race', also works with full spreadsheet
def gen_stats(racelist,racename):
    race_count = 0 #just used for checking, ignore error with all cars
    papers_shelter_list = []
    no_papers_shelter_list = []
    not_inspected_shelter_list = []
    inspected_shelter_list = []
    ok_shelter_list = []
    results = []
    weighed = {"Race": [], "Practice": []}

    if DEBUG:
        print "DEBUG: Stats generator got %d rows" % len(racelist)

    # iterate through all cars in the given race, ignore car 0 because
    # that is a dummy to provide the SR requirements for that race
    # append to shelter lists, to remove duplication for race/practice.
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        # first check the HTP number field
        if (car[HTP_NO] != "") and (car[HTP_NO] != "No Papers"):
            if car[SHELTER] not in papers_shelter_list:
                papers_shelter_list.append(car[SHELTER])

    # then check for No Papers - done seperately in case it is recorded as no
    # papers and then papers were later found
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        # first check the HTP number field
        if car[HTP_NO] == "No Papers" or car[HTP_NO] == "":
            if (car[SHELTER] not in papers_shelter_list) and (car[SHELTER] not in no_papers_shelter_list):
                no_papers_shelter_list.append(car[SHELTER])

    # find cars that we scruitineered but did not capture paper information for
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        for cell in range(FIRST_DATA_CELL,len(car)):
            if (car[cell] != "") and (car[SHELTER] not in inspected_shelter_list):
                inspected_shelter_list.append(car[SHELTER])
    
    # find cars that are checked OK
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        if car[CHECKED] == "OK":
            if (car[SHELTER] not in papers_shelter_list) and (car[SHELTER] not in no_papers_shelter_list):
                no_papers_shelter_list.append(car[SHELTER])

    # finally find cars we have not inspected
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        if (car[SHELTER] not in inspected_shelter_list) and (car[SHELTER] not in not_inspected_shelter_list):
                not_inspected_shelter_list.append(car[SHELTER])

    # find cars we have weighed
    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        if car[WEIGHT_ACTUAL] != "":
            weighed[car[RACE_PRACTICE]].append(car[SHELTER])

    for car in racelist:
        if car[CAR_NO] == "0":
            continue
        if car[RACE_PRACTICE] == "Race":
            race_count += 1
    # do basic consistency check, this will break if fed list of all cars and they appear in multiple races
    if len(inspected_shelter_list) + len(not_inspected_shelter_list) != race_count:
        if DEBUG:
            print "WARNING: Count(%d) of race cars in _%s_ does not equal sum(%d) of inspected(%d) and not inspected(%d) cars, possible program error" % (race_count, racename,(len(inspected_shelter_list) + len(not_inspected_shelter_list)), len(inspected_shelter_list), len(not_inspected_shelter_list))

    # stick results in a list of lists, so we can either print or CSV easily
    results.append([racename,""])
    results.append(["Total in race",(len(inspected_shelter_list) + len(not_inspected_shelter_list))])
    results.append(["Inspected",len(inspected_shelter_list)])
    results.append(["Not inspected",len(not_inspected_shelter_list)])
    results.append(["Has papers",len(papers_shelter_list)])
    results.append(["No papers",len(no_papers_shelter_list)])
    results.append(["Weighed (unique cars)",len(set.union(set(weighed["Race"]), set(weighed["Practice"])))])
    results.append(["Weighed after Practice",len(weighed["Practice"])])
    results.append(["Weighed after Race",len(weighed["Race"])])


    return results

# check compliance with car 0 - TBD work out how to handle weights
# Racelist is a list of lists containing race cars
# racename is a string with the name of the race e.g. 'github trophy'
# key_line is a list of column titles
def check_compliance(racelist,racename,key_line):
    checked_columns = {"Race" : [], "Practice" : []}
    results = {"Race" : [], "Practice" : []}
    CHECK = OWNER + 1
    SR_CHECK = OWNER + 2
    INFRACTION_LIST = OWNER + 3
    SR_INFRACTION_LIST = OWNER + 4
    WEIGHT = SR_INFRACTION_LIST + 1
    sr_notes = ""


    if DEBUG:
        print "DEBUG: checking compliance for %s" % racename

    # build check column list from car zero
    for car in racelist:
        if car[CAR_NO] == "0":
            for column in range(FIRST_DATA_CELL,len(car)):
                if car[column] == "OK":
                    checked_columns[car[RACE_PRACTICE]].append(column)
            sr_notes = car[NOTES]

    if DEBUG:
        print "DEBUG: SR columns from car zero in %s" % racename
        print checked_columns

    #iterate through cars
    for car in racelist:
        check_count = 0
        non_compliant = []
        sr_check_count = 0
        sr_non_compliant = []
        weight = 0

        if car[CAR_NO] == "0":
            continue

        # Check columns identified in SRs using car 0
        for column in range(FIRST_DATA_CELL,len(car)):
            if car[column] != "":
                #its not blank, so something is recorded
                if car[column] == "OK":
                    if column in checked_columns[car[RACE_PRACTICE]]:
                        # If its in the list of columns from car zero, add to SR check
                        sr_check_count += 1
                    else:
                        # Otherwise just add it to the list of other checks
                        check_count += 1
                elif "NO -" in car[column]:
                    if column in checked_columns[car[RACE_PRACTICE]]:
                        sr_check_count += 1
                        sr_non_compliant.append([column,car[column].split("- ")[1]])
                    else:
                        check_count += 1
                        non_compliant.append([column,car[column].split("- ")[1]])
                #Handle weight in else statement here?
                if column == WEIGHT_ACTUAL:
                    weight = car[column].split(" ")[0]

        # if there are any checks completed for this car, store results
        if check_count + sr_check_count + float(weight) > 0:
            result = []
            #copy in details up to the owner field
            for cell in range(0, OWNER + 1):
                result.append(car[cell])
            result.append(check_count)
            result.append(sr_check_count)
            result.append(non_compliant)
            result.append(sr_non_compliant)
            result.append(weight)
            results[car[RACE_PRACTICE]].append(result)
        # check other columns that may have been inspected

    # print notes from car zero to explain checks
    print "%s" % sr_notes.replace("  ",", ")
    print ""
    print "###Compliance check results:"
    for key in ["Practice", "Race"]:
        # print race or practise
        print "####%s:" % key
        for car in results[key]:
            # Print the results of the SR checks
            print "#####Car %s: %s %s (%s) - shelter %s" % (car[CAR_NO], car[YEAR], car[CAR_MODEL], car[OWNER].replace("  ",", "), car[SHELTER])
            if car[WEIGHT] != 0:
                print "* Checked weight: %skg" % car[WEIGHT]

            if car[SR_CHECK] > 0:
                if len(car[SR_INFRACTION_LIST]) == 0:
                    print "* Checked %d supplementary regulations, %d infractions" % (car[SR_CHECK],len(car[SR_INFRACTION_LIST]))
                elif len(car[SR_INFRACTION_LIST]) == 1:
                    print "* Checked %d supplementary regulations, %d infraction:" % (car[SR_CHECK],len(car[SR_INFRACTION_LIST]))
                else:
                    print "* Checked %d supplementary regulations, %d infractions:" % (car[SR_CHECK],len(car[SR_INFRACTION_LIST]))

            for infraction in car[SR_INFRACTION_LIST]:
                # take the check category (engine, suspension, etc) from the key_line and print with infraction
                print "1. %s: %s" % (key_line[infraction[0]], infraction[1])
            
            # Print the result of other checks
            if car[CHECK] > 0:
                if len(car[INFRACTION_LIST]) == 0:
                    print "* Checked %d other regulations/specifications/requirements, %d infractions" % (car[CHECK],len(car[INFRACTION_LIST]))
                elif len(car[INFRACTION_LIST]) == 1:
                    print "* Checked %d other regulations/specifications/requirements, %d infraction:" % (car[CHECK],len(car[INFRACTION_LIST]))
                else:
                    print "* Checked %d other regulations/specifications/requirements, %d infractions:" % (car[CHECK],len(car[INFRACTION_LIST]))

            for infraction in car[INFRACTION_LIST]:
                # take the check category (engine, suspension, etc) from the key_line and print with infraction
                print "1. %s: %s" % (key_line[infraction[0]], infraction[1])

            print ""


# print results
def print_results(results_list):
    print "## " + results_list[0][0]
    for row in results_list[1:]:
        print ("- %s:  %d") % (row[0], row[1])
    print ""




#Load the CSV and split it up into a dictionary indexed by race names
raw_csv = readcsv("77mm.csv")
split_by_race = split_race(raw_csv)

#Get race stats for all races
race_stats = gen_stats(raw_csv[1:], "All races")

print "# Eligibility Scruitineering results"
print_results(race_stats)

exit()

#uncomment and complete 'name' with a race name to check compliance for a single race

#name = ""
#check_compliance(split_by_race[name], name, raw_csv[0])

#Get stats per race and list compliance
for race in split_by_race.keys():
    race_stats = gen_stats(split_by_race[race], race)
    print_results(race_stats)
    check_compliance(split_by_race[race], race, raw_csv[0])
