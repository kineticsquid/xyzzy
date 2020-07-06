import json
import io
import re

INPUT_FILE = '../Original_source/advent.dat'

LINSIZ = 9650
TRVSIZ = 750
TABSIZ = 300
LOCSIZ = 150
VRBSIZ = 35
RTXSIZ = 205
CLSMAX = 12
HNTSIZ = 20
MAGSIZ = 35

# These are for data in section 9
LIGHT = 0
OIL_WATER = 1
LIQUID = 2
NO_PIRATE = 3
TRYING_TO_ENTER_CAVE = 4
TRYING_TO_GET_BIRD = 5
TRYING_TO_DEAL_WITH_SNAKE = 6
LIST_IN_MAZE = 7
PONDERING_DARK_ROOM = 8
AT_WITTS_END = 9

def parse_line(input_file_line):
    regex = '(\d+)(.+)'
    match = re.findall(regex, input_file_line)
    if match is not None:
        number = int(match[0][0])
        text = match[0][1].strip()
        return number, text
    else:
        return None, None

def read_input_file(input_file_name):
    input_file = open(INPUT_FILE, 'r')

    # Read long descriptions
    # SECTION 1: LONG FORM DESCRIPTIONS.  EACH LINE CONTAINS A LOCATION NUMBER,
    # A TAB, AND A LINE OF TEXT.  THE SET OF (NECESSARILY ADJACENT) LINES
    # WHOSE NUMBERS ARE X FORM THE LONG DESCRIPTION OF LOCATION X.
    #
    # Skip over the first line in the input file, which is just the number '1' indicating the start of the first
    # section of data
    input_file.readline()
    LTEXT_long_descriptions = {}
    current_line = ''
    current_number = 0
    for line in input_file:
        if line.find('-1') >= 0:
            LTEXT_long_descriptions[current_number] = current_line
            break
        else:
            new_number, text = parse_line(line)
            if current_number == 0:
                current_line = text
                current_number = new_number
            elif new_number == current_number:
                current_line = current_line + ' ' + text
            else:
                LTEXT_long_descriptions[current_number] = current_line
                current_line = text
                current_number = new_number


    # Read short descriptions
    # SECTION 2: SHORT FORM DESCRIPTIONS.  SAME FORMAT AS LONG FORM.  NOT ALL
    # PLACES HAVE SHORT DESCRIPTIONS.
    #
    # Skip over the next line in the input file, which is just the number '2' indicating the start of the second
    # section of data
    input_file.readline()
    STEXT_short_descriptions = {}
    for line in input_file:
        if line.find('-1') >= 0:
            break
        else:
            number, text = parse_line(line)
            STEXT_short_descriptions[number] = text


    # Read map data
    # SECTION 3: TRAVEL TABLE.  EACH LINE CONTAINS A LOCATION NUMBER (X), A SECOND
    # LOCATION NUMBER (Y), AND A LIST OF MOTION NUMBERS (SEE SECTION 4).
    # EACH MOTION REPRESENTS A VERB WHICH WILL GO TO Y IF CURRENTLY AT X.
    # Y, IN TURN, IS INTERPRETED AS FOLLOWS.  LET M=Y/1000, N=Y MOD 1000.
    #   IF N<=300 IT IS THE LOCATION TO GO TO.
    #   IF 300<N<=500 N-300 IS USED IN A COMPUTED GOTO TO
    #         A SECTION OF SPECIAL CODE.
    #   IF N>500  MESSAGE N-500 FROM SECTION 6 IS PRINTED,
    #         AND HE STAYS WHEREVER HE IS.
    # MEANWHILE, M SPECIFIES THE CONDITIONS ON THE MOTION.
    #   IF M=0    IT'S UNCONDITIONAL.
    #   IF 0<M<100  IT IS DONE WITH M% PROBABILITY.
    #   IF M=100  UNCONDITIONAL, BUT FORBIDDEN TO DWARVES.
    #   IF 100<M<=200 HE MUST BE CARRYING OBJECT M-100.
    #   IF 200<M<=300 MUST BE CARRYING OR IN SAME ROOM AS M-200.
    #   IF 300<M<=400 PROP(M MOD 100) MUST *NOT* BE 0.
    #   IF 400<M<=500 PROP(M MOD 100) MUST *NOT* BE 1.
    #   IF 500<M<=600 PROP(M MOD 100) MUST *NOT* BE 2, ETC.
    # IF THE CONDITION (IF ANY) IS NOT MET, THEN THE NEXT *DIFFERENT*
    # "DESTINATION" VALUE IS USED (UNLESS IT FAILS TO MEET *ITS* CONDITIONS,
    # IN WHICH CASE THE NEXT IS FOUND, ETC.).  TYPICALLY, THE NEXT DEST WILL
    # BE FOR ONE OF THE SAME VERBS, SO THAT ITS ONLY USE IS AS THE ALTERNATE
    # DESTINATION FOR THOSE VERBS.  FOR INSTANCE:
    #   15  110022  29  31  34  35  23  43
    #   15  14  29
    # THIS SAYS THAT, FROM LO# 15, ANY OF THE VERBS 29, 31, ETC., WILL TAKE
    # HIM TO 22 IF HE'S CARRYING OBJECT 10, AND OTHERWISE WILL GO TO 14.
    #   11  303008  49
    #   11  9 50
    # THIS SAYS THAT, FROM 11, 49 TAKES HIM TO 8 UNLESS PROP(3)=0, IN WHICH
    # CASE HE GOES TO 9.  VERB 50 TAKES HIM TO 9 REGARDLESS OF PROP(3).
    #
    # The structure of the input lines is as follows:
    #
    #   [current_location] [new_location] [ATAB_vocabulary that get one from current to new location]
    #
    # This is represneted in TRAVEL_map_data. Structure of TRAVEL_map_data is as follows:
    #
    #   { location1 :
    #       { command: new_location,
    #         command: new_location},
    #     location2 :
    #       { command: new_location}
    #     ...
    #   }
    #
    # Skip over the next line in the input file, which is just the number '3' indicating the start of the third
    # section of data.
    input_file.readline()
    TRAVEL_map_data = {}
    regex = '(\d+)'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            match = re.findall(regex, line)
            from_room = int(match[0])
            to_room = int(match[1])
            # means is the vocabulary word or command that gets one from from_room to to_room
            means = match[2:len(match)]
            if TRAVEL_map_data.get(from_room, None) is None:
                TRAVEL_map_data[from_room] = {}
            for m in means:
                TRAVEL_map_data[from_room][int(m)] = to_room

    # Read keywords
    # SECTION 4: VOCABULARY.  EACH LINE CONTAINS A NUMBER (N), A TAB, AND A
    # FIVE-LETTER WORD.  CALL M=N/1000.  IF M=0, THEN THE WORD IS A MOTION
    # VERB FOR USE IN TRAVELLING (SEE SECTION 3).  ELSE, IF M=1, THE WORD IS
    # AN OBJECT.  ELSE, IF M=2, THE WORD IS AN ACTION VERB (SUCH AS "CARRY"
    # OR "ATTACK").  ELSE, IF M=3, THE WORD IS A SPECIAL CASE VERB (SUCH AS
    # "DIG") AND N MOD 1000 IS AN INDEX INTO SECTION 6.  OBJECTS FROM 50 TO
    # (CURRENTLY, ANYWAY) 79 ARE CONSIDERED TREASURES (FOR PIRATE, CLOSEOUT).
    #
    # Skip over the next line in the input file, which is just the number '4' indicating the start of the fourth
    # section of data.
    input_file.readline()
    ATAB_vocabulary = {}
    for line in input_file:
        if line.strip() == '-1': break
        else:
            number, command = parse_line(line)
            ATAB_vocabulary[command] = number

    # Read object descriptions
    # SECTION 5: OBJECT DESCRIPTIONS.  EACH LINE CONTAINS A NUMBER (N), A TAB,
    # AND A MESSAGE.  IF N IS FROM 1 TO 100, THE MESSAGE IS THE "INVENTORY"
    # MESSAGE FOR OBJECT N.  OTHERWISE, N SHOULD BE 000, 100, 200, ETC., AND
    # THE MESSAGE SHOULD BE THE DESCRIPTION OF THE PRECEDING OBJECT WHEN ITS
    # PROP VALUE IS N/100.  THE N/100 IS USED ONLY TO DISTINGUISH MULTIPLE
    # MESSAGES FROM MULTI-LINE MESSAGES; THE PROP INFO ACTUALLY REQUIRES ALL
    # MESSAGES FOR AN OBJECT TO BE PRESENT AND CONSECUTIVE.  PROPERTIES WHICH
    # PRODUCE NO MESSAGE SHOULD BE GIVEN THE MESSAGE ">$<".
    #
    # The object descriptions from the input file are represented as follows
    #
    # {object_number :
    #   { 'text' : description,
    #       0   : description when object property (PROP) value is 0,
    #       1   : description when PROP is 1
    #   },
    #   object_number2 :
    #   {'text' : description,
    #   ...}
    #  }
    #
    # Skip over the next line in the input file, which is just the number '5' indicating the start of the fifth
    # section of data.
    input_file.readline()
    PTEXT_object_descriptions = {}
    current_object = None
    regex = '(\d+)(.+)'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            number, text = parse_line(line)
            if len(match[0][0]) < 3:
                current_object = number
                PTEXT_object_descriptions[current_object] = {'text': text}
            else:
                PTEXT_object_descriptions[current_object][int(number/100)] = text

    # Read game states
    # SECTION 6: ARBITRARY MESSAGES.  SAME FORMAT AS SECTIONS 1, 2, AND 5, EXCEPT
    # THE NUMBERS BEAR NO RELATION TO ANYTHING (EXCEPT FOR SPECIAL VERBS
    # IN SECTION 4).
    #
    # Skip over the next line in the input file, which is just the number '6' indicating the start of the sixth
    # section of data.
    input_file.readline()
    RTEXT_arbitrary_messages = {}
    current_line = ''
    current_number = 0
    for line in input_file:
        if line.find('-1') >= 0:
            RTEXT_arbitrary_messages[current_number] = current_line
            break
        else:
            new_number, text = parse_line(line)
            if current_number == 0:
                current_line = text
                current_number = new_number
            elif new_number == current_number:
                current_line = current_line + ' ' + text
            else:
                RTEXT_arbitrary_messages[current_number] = current_line
                current_line = text
                current_number = new_number

    # Read object locations
    # SECTION 7: OBJECT LOCATIONS.  EACH LINE CONTAINS AN OBJECT NUMBER AND ITS
    # INITIAL LOCATION (ZERO (OR OMITTED) IF NONE).  IF THE OBJECT IS
    # IMMOVABLE, THE LOCATION IS FOLLOWED BY A "-1".  IF IT HAS TWO LOCATIONS
    # (E.G. THE GRATE) THE FIRST LOCATION IS FOLLOWED WITH THE SECOND, AND
    # THE OBJECT IS ASSUMED TO BE IMMOVABLE.
    #
    # { object1:
    #   { 'PLAC': object_location,
    #     'FIXD': object_location | -1 },
    #   object2:
    #   { ... }
    # }
    # Skip over the next line in the input file, which is just the number '7' indicating the start of the seventh
    # section of data.
    input_file.readline()
    object_locations = {}
    regex = '-*\d+'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            match = re.findall(regex, line)
            if match is not None and len(match) > 1:
                object = int(match[0])
                PLAC = int(match[1])
                object_locations[object] = {'PLAC': PLAC}
                if len(match) == 3:
                    FIXD = int(match[2])
                    object_locations[object]['FIXD'] = FIXD

    # Read messages for action verbs
    # SECTION 8: ACTION DEFAULTS.  EACH LINE CONTAINS AN "ACTION-VERB" NUMBER AND
    # THE INDEX (IN SECTION 6) OF THE DEFAULT MESSAGE FOR THE VERB.
    #
    # Skip over the next line in the input file, which is just the number '8' indicating the start of the eigth
    # section of data.
    input_file.readline()
    ACTSPK_verb_messages = {}
    regex = '-*\d+'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            match = re.findall(regex, line)
            if match is not None and len(match) == 2:
                object = int(match[0])
                message_index = int(match[1])
                ACTSPK_verb_messages[object] = message_index

    # Read location conditions
    # SECTION 9: LIQUID ASSETS, ETC.  EACH LINE CONTAINS A NUMBER (N) AND UP TO 20
    # LOCATION NUMBERS.  BIT N (WHERE 0 IS THE UNITS BIT) IS SET IN COND(LOC)
    # FOR EACH LO# GIVEN.  THE COND BITS CURRENTLY ASSIGNED ARE:
    #   0 LIGHT
    #   1 IF BIT 2 IS ON: ON FOR OIL, OFF FOR WATER
    #   2 LIQUID ASSET, SEE BIT 1
    #   3 PIRATE DOESN'T GO HERE UNLESS FOLLOWING PLAYER
    # OTHER BITS ARE USED TO INDICATE AREAS OF INTEREST TO "HINT" ROUTINES:
    #   4 TRYING TO GET INTO CAVE
    #   5 TRYING TO CATCH BIRD
    #   6 TRYING TO DEAL WITH SNAKE
    #   7 LOST IN MAZE
    #   8 PONDERING DARK ROOM
    #   9 AT WITT'S END
    # COND(LOC) IS SET TO 2, OVERRIDING ALL OTHER BITS, IF LO# HAS FORCED
    # MOTION.
    #
    # Rather than setting bits, structure is a dictionary of locations with associated tuples containing the
    # relevant conditions.
    #
    # Skip over the next line in the input file, which is just the number '9' indicating the start of the ninth
    # section of data.
    input_file.readline()
    COND_location_conditions = {}
    regex = '-*\d+'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            match = re.findall(regex, line)
            if match is not None and len(match) > 1:
                COND = int(match[0])
                for m in range(1,len(match)):
                    location = int(match[m])
                    if COND_location_conditions.get(location, None) is None:
                        COND_location_conditions[location] = (COND,)
                    else:
                        COND_location_conditions[location] = COND_location_conditions[location] + (COND,)

    # Read location conditions
    #
    # SECTION 10: CLASS MESSAGES.  EACH LINE CONTAINS A NUMBER (N), A TAB, AND A
    # MESSAGE DESCRIBING A CLASSIFICATION OF PLAYER.  THE SCORING SECTION
    # SELECTS THE APPROPRIATE MESSAGE, WHERE EACH MESSAGE IS CONSIDERED TO
    # APPLY TO PLAYERS WHOSE SCORES ARE HIGHER THAN THE PREVIOUS N BUT NOT
    # HIGHER THAN THIS N.  NOTE THAT THESE SCORES PROBABLY CHANGE WITH EVERY
    # MODIFICATION (AND PARTICULARLY EXPANSION) OF THE PROGRAM.
    #
    # Skip over the next line in the input file, which is just the number '10' indicating the start of the tenth
    # section of data.
    input_file.readline()
    CTEXT_class_messages = {}
    for line in input_file:
        if line.strip() == '-1': break
        else:
            number, text = parse_line(line)
            CTEXT_class_messages[number] = text

    # Read hints
    #
    # SECTION 11: HINTS.  EACH LINE CONTAINS A HINT NUMBER (CORRESPONDING TO A
    # COND BIT, SEE SECTION 9), THE NUMBER OF TURNS HE MUST BE AT THE RIGHT
    # LOC(S) BEFORE TRIGGERING THE HINT, THE POINTS DEDUCTED FOR TAKING THE
    # HINT, THE MESSAGE NUMBER (SECTION 6) OF THE QUESTION, AND THE MESSAGE
    # NUMBER OF THE HINT.  THESE VALUES ARE STASHED IN THE "HINTS" ARRAY.
    # HNTMAX IS SET TO THE MAX HINT NUMBER (<= HNTSIZ).  NUMBERS 1-3 ARE
    # UNUSABLE SINCE COND BITS ARE OTHERWISE ASSIGNED, SO 2 IS USED TO
    # REMEMBER IF HE'S READ THE CLUE IN THE REPOSITORY, AND 3 IS USED TO
    # REMEMBER WHETHER HE ASKED FOR INSTRUCTIONS (GETS MORE TURNS, BUT LOSES
    # POINTS).
    #
    # Skip over the next line in the input file, which is just the number '11' indicating the start of the eleventh
    # section of data.
    input_file.readline()
    HINTS_messages = {}
    regex = '-*\d+'
    for line in input_file:
        if line.strip() == '-1': break
        else:
            match = re.findall(regex, line)
            if match is not None and len(match) > 1:
                COND = int(match[0])
                for m in range(1,len(match)):
                    location = int(match[m])
                    if HINTS_messages.get(COND, None) is None:
                        HINTS_messages[COND] = (location,)
                    else:
                        HINTS_messages[COND] = HINTS_messages[COND] + (location,)

    # Input magic messages
    #
    # SECTION 12: MAGIC MESSAGES. IDENTICAL TO SECTION 6 EXCEPT PUT IN A SEPARATE
    # SECTION FOR EASIER REFERENCE.  MAGIC MESSAGES ARE USED BY THE STARTUP,
    # MAINTENANCE MODE, AND RELATED ROUTINES.
    #
    # Skip over the next line in the input file, which is just the number '11' indicating the start of the eleventh
    # section of data.
    input_file.readline()
    MTEXT_magic_messages = {}
    for line in input_file:
        if line.strip() == '-1': break
        else:
            number, text = parse_line(line)
            MTEXT_magic_messages[number] = text

    # SECTION 0: END OF DATABASE.
    #  READ THE DATABASE IF WE HAVE NOT YET DONE SO



    return LTEXT_long_descriptions, STEXT_short_descriptions, TRAVEL_map_data, keywords, game_states, hints_and_events

def main():
    try:

        long_descriptions, short_descriptions, map_data, keywords, game_states, hints_and_events = read_input_file(INPUT_FILE)


    except Exception as e:
        print('Error: ' + str(e))


if __name__ == '__main__':
    main()


