#!/usr/bin/env python3
"""Make some plots of the class enrollment data"""

__author__="Tyler Westland"

import argparse
from dataclasses import dataclass, field
import json
import matplotlib.pyplot as plt
import os
import sys


@dataclass(frozen=True)
class Course:
    department: str
    number: int
    extra_number_info: str
    name: str
    section: int
    capacity: int
    enrolled: int
    wait_list_capacity: int
    wait_list_total: int

    @classmethod
    def from_dict(cls, d:dict) -> "Course":
        return cls(
                d["department"],
                int(d["number"]),
                d["extra_number_info"],
                d["name"],
                int(d["section"]),
                int(d["capacity"]),
                int(d["enrolled"]),
                int(d["wait list capacity"]),
                int(d["wait list total"])
                )

    @property
    def enrollement_ratio(self) -> float:
        return self.enrolled / self.capacity

def box_plot(output_name, x_name, x_data, show):
    fig, ax = plt.subplots()
    ax.boxplot(x_data, vert=False)

    ax.set_title(f"{x_name}")

    if show:
        plt.show()
    fig.savefig(output_name)
    plt.close()

def bar_plot(output_name, x_name, y_name, y_data, tick_label, title, show):
    fig, ax = plt.subplots()
    ax.bar(list(range(len(y_data))), y_data, tick_label=tick_label)

    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_title(title)

    if show:
        plt.show()
    fig.savefig(output_name)
    plt.close()


def parse_arguments(args=None) -> argparse.Namespace:
    """Returns the parsed arguments.
    Parameters
    ----------
    args: List of strings to be parsed by argparse.
        The default None results in argparse using the values passed into
        sys.args.
    """
    parser = argparse.ArgumentParser(
            description="Make some plots of the class enrollment data",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-df","--data_file", help="Path to the data file.",
                        default="./class_enrollment.json")
    parser.add_argument("-s", "--show", help="Interactively show the plots",
                        default=False, action="store_true")
    args = parser.parse_args(args=args)
    return args


def main(data_file:str="./class_enrollment.json", show: bool=False) -> None:
    """Main function.

    Parameters
    ----------
    data_file: str
        Path to the data file.
    show: bool=False
        Rather to show the plots interactively.
    Returns
    -------
    ???
        Something useful.
    Raises
    ------
    FileNotFoundError
        Means that the input file was not found.
    """
    # Error check if the file even exists
    if not os.path.isfile(data_file):
        raise FileNotFoundError("File not found: {}".format(input_file))

    # Read in the data
    with open(data_file) as fin:
        enrollment = json.load(fin)

    # Change each dict into a proper class
    for i in range(len(enrollment["class information"])):
        enrollment["class information"][i] = Course.\
                from_dict(enrollment["class information"][i])

    box_plot("undergrad.png", "Undergrad Enrollment", 
             [course.enrollement_ratio for course in 
               filter(lambda course: course.number < 6000, 
                      enrollment["class information"])
             ],
             show)
    box_plot("grad.png", "Grad Enrollment", 
             [course.enrollement_ratio for course in 
               filter(lambda course: course.number >= 6000, 
                      enrollment["class information"])
             ],
             show)
    box_plot("all.png", "All Enrollment", 
             [course.enrollement_ratio for course in 
                enrollment["class information"]
             ],
             show)

    # Count up number of courses
    number_of_courses = {}
    for course_range in range(1000,8000,1000):
        number_of_courses[course_range] = len(list(filter(
            lambda course: course_range <= course.number < course_range + 1000,
            enrollment["class information"]
            )))

    bar_plot("number_of_courses_per_range.png", "Course Numbers", 
             "Number of Courses", list(number_of_courses.values()), 
             list(str(n) for n in number_of_courses), 
             "Number of Courses Per Range", show)

    number_of_courses_per_career = {
            "undergrad exclusive": sum(number_of_courses[ran] for ran in 
                                        filter(lambda ran: ran < 5000,
                                               number_of_courses)),
            "combined": sum(number_of_courses[ran] for ran in 
                                        filter(lambda ran: 5000 <= ran <= 6000,
                                               number_of_courses)),
            "grad exclusive": sum(number_of_courses[ran] for ran in 
                                        filter(lambda ran: ran > 6000,
                                               number_of_courses))
            }

    bar_plot("number_of_courses_per_career.png", "Course Numbers", 
             "Number of Courses", list(number_of_courses_per_career.values()), 
             list(str(n) for n in number_of_courses_per_career), 
             "Number of Courses Per Career", show)

    return None


def cli_interface() -> None:
    """Get program arguments from command line and run main"""
    args = parse_arguments()
    try:
        main(**vars(args))
        sys.exit(0)
    except FileNotFoundError as exp:
        print(exp, file=sys.stderr)
        sys.exit(1)


# Execute only if this file is being run as the entry file.
if __name__ == "__main__":
    cli_interface()
