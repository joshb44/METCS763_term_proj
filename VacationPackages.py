# Represents destionations for which the travel agency currently has a package
# available, along with the qualities the agency has decided to associate with
# each locale based its inherent nature and on the package's offerings
class VacationPackages:
    def __init__(self):

        self.destinations = {

            "Hawaii": ["Relaxing", "Adventurous", "Exploratory",
                       "Beach", "Alone", "With Spouse"],
            "Rome": ["Adventurous", "Exploratory", "Culinary"
                       "Urban", "Alone", "With Spouse"],
            "Disneyland": ["Adventurous", "Urban", "With Family"]
        }