# Represents destinations for which the travel agency currently has a package
# available, along with the qualities the agency has decided to associate with
# each locale based its inherent nature and on the package's offerings.
# Also denotes the tone to use when describing packages of a certain type.
class VacationPackages:
    def __init__(self):
        self.destinations = {

            "Hawaii": ["Relaxing", "Adventurous", "Exploratory",
                       "Beach", "Alone", "With Significant Other"],

            "Rome": ["Adventurous", "Exploratory", "Dining",
                     "Urban", "Alone", "With Significant Other"],

            "Disneyland": ["Adventurous", "Urban", "With Family"],

            "Hoosier National Forest": ["Adventurous", "Exploratory",
                                        "Wilderness", "Alone", "With Friends"],

            "The Land Between The Lakes": ["Adventurous", "Exploratory",
                                           "Beach", "Wilderness",
                                           "With Friends", "With Family"],
            "Brown County State Park": ["Relaxing", "Exploratory",
                                        "Wilderness", "Alone", "With Family",
                                        "With Significant Other",
                                        "With Friends"]
        }

        self.tones = {

            "Relaxing": "Soothing",
            "Adventurous": "Excited",
            "Dining": "Savoring",
            "Exploratory": "Intriguing"

        }
