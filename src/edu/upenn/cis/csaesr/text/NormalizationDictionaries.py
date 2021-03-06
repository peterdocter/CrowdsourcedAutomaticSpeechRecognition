"""Dictionaries for transcription normalization."""
# Copyright (C) 2014 Taylor Turpen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

schematic_schematic = {"INPUT":{type:{dict:[]}}}
#===============================================================================
# for func_param in schematic:
#     for definitions in func_param:
#         for definition in func_param[definitions]:
#             if definition == type:
#                 type_def = func_param[definitions][definition]
#===============================================================================
#===============================================================================
# schematic = {"SCHEMATIC": {"INPUT":{"orig":{"type":{"list":"string"}},
#                                         "correct":{"type":{"list":"string"},}}
#                                }
#===============================================================================
example_sents ={"hyphen": {"orig":[ "REDRAW" , "CHART" , "OF" , "MOZAMBIQUE" , "CHANNEL" , "WITH" , "BUD-TEST" , "OVERLAY" , "ADDED"],
                            "correct": [ "redraw" , "chart" , "of" , "mozambique" , "channel" , "with" , "bud","test" , "overlay" , "added"]}}

singles = {"OTHER": "",
           "1": "one",
           "2": "two",
           "3": "three",
           "4": "four",
           "5": "five",
           "6": "six",
           "7": "seven",
           "8": "eight",
           "9": "nine"}
suffixes = ["th","nd","rd","st"]

ones = [("",""),("one","first"),("two","second"),("three","third"),("four","fourth"),
        ("five","fifth"),("six","sixth"),("seven","seventh"),("eight","eighth"),("nine","ninth")]
teens = [("eleven","eleventh"),("twelve","twelfth"),("thirteen","thirteenth"),("fourteen","fourteenth"),
        ("fifteen","fifteenth"),("sixteen","sixteenth"),("seventeen","seventeenth"),("eighteen","eighteenth"),("nineteen","nineteenth")]
tens = ["","","twenty","thirty","forty","fifty","sixty","seventy","eighty","ninety"]

places = ["hundred","thousand"]

ones_tens_dict ={    "th":{  "4" : {"1": "fourteenth",
                                    "OTHER" : "forth"},
                            "5" : {"1" : "fifteenth",
                                   "OTHER" :"fifth"},
                            "6" : {"1" : "sixteenth",
                                   "OTHER" : "sixth"},
                            "7" : {"1" : "seventeenth",
                                   "OTHER" : "seventh"},
                            "8" : {"1" : "eighteenth",
                                   "OTHER" : "eighth"},
                            "9" : {"1" : "nineteenth",
                                   "OTHER" : "ninth"},
                            "2" : {"1": "twelfth"},
                            "1" : {"1": "eleventh"},
                            "0" : {"2" : "twentieth",
                                   "3" : "thirtieth",
                                   "4" : "fortieth",
                                    "5" : "fiftieth",
                                    "6" : "sixtieth" ,
                                    "7" : "seventieth",
                                    "8" : "eightieth",
                                    "9" : "ninetieth",
                                    "OTHER":""}
                                       },                        
                    "nd": {"2": {"OTHER" :"second"}},
                    "rd": {"3" : {"OTHER" : "third"}},
                    "st": {"1" : {"OTHER" : "first"}},
                    "1" : {"1" : "eleven",
                           "OTHER" : "one"},
                    "2" : {"1" : "twelve",
                       "OTHER" : "two"},
                    "3" : {"1" : "thirteen",
                       "OTHER" : "three"},
                    "4" : {"1" : "forteen",
                       "OTHER" : "four"},
                    "5" : {"1" : "fifteen",
                       "OTHER" : "five"},
                    "6" : {"1" : "sixteen",
                       "OTHER" : "six"},
                    "7" : {"1" : "seventeen",
                       "OTHER" : "seven"},
                    "8" : {"1" : "eighteen",
                       "OTHER" : "eight"},
                    "9" : {"1" : "nineteen",
                       "OTHER" : "nine"},
                    "0" : {"2" : "twenty",
                           "3" : "thirty",
                           "4" : "forty",
                           "5" : "fifty",
                           "6" : "sixty" ,
                           "7" : "seventy",
                           "8" : "eighty",
                           "9" : "ninety",
                           "1" : "ten",
                           "OTHER": ""},
                    "OTHER" : ""
                    }
    