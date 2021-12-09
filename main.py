#!/usr/bin/env python3
"""Make some plots of the class enrollment data"""

__author__="Tyler Westland"

import argparse
from dataclasses import dataclass, field
import itertools
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from typing import List


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


@dataclass(frozen=True)
class CourseCatalog:
    semester_year:int
    semester_season: str
    courses: List[Course]

    @property
    def semester_name(self) -> str:
        return f"{self.semester_season}-{self.semester_year}"

    def enrollment_plots(self, show: bool) -> None:
        box_plot(f"{self.semester_name}--undergrad.png",
                 f"{self.semester_name} Undergrad Courses", 
                 [course.enrollement_ratio for course in 
                   filter(lambda course: course.number < 6000, 
                          self.courses)
                 ],
                 show)
        box_plot(f"{self.semester_name}--grad.png",
                 f"{self.semester_name} Grad Courses", 
                 [course.enrollement_ratio for course in 
                   filter(lambda course: course.number >= 6000, 
                          self.courses)
                 ],
                 show)
        box_plot(f"{self.semester_name}--all.png",
                 f"{self.semester_name} All Courses", 
                 [course.enrollement_ratio for course in 
                   self.courses
                 ],
                 show)

    def available_courses_plots(self, show: bool) -> None:
        courses_by_level = self.courses_by_level(max_level=7000)
        bar_plot(f"{self.semester_name}--number_of_courses_per_level.png", 
                 f"{self.semester_name} Course Levels", "Number of Courses", 
                 list(len(level) for level in courses_by_level.values()), 
                 list(str(n) for n in courses_by_level), 
                 "Number of Courses Per Level", show)

        by_career = self.courses_by_career()
        bar_plot(f"{self.semester_name}--number_of_courses_per_career.png", 
                 f"{self.semester_name} Career", "Number of Course",
                 list(len(courses) for courses in by_career.values()), 
                 list(str(n) for n in by_career), 
                 "Number of Courses Per Career", show)

    @classmethod
    def from_dict(cls, d:dict) -> "CourseCatalog":
        return cls(
                int(d["semester_year"]),
                d["semester_season"],
                list(Course.from_dict(dc) for dc in d["class information"])
                )

    def courses_in_level(self, level: int):
        return list(filter(
                lambda course: level <= course.number < level + 1000,
                self.courses
               ))

    def courses_by_level(self, min_level: int = 1000, max_level: int = 9000):
        courses_by_level = {}
        for level in range(min_level, max_level + 1000, 1000):
            courses_by_level[level] = self.courses_in_level(level)
        return courses_by_level

    def courses_by_career(self):
        by_career = {
            "undergrad exclusive": list(itertools.chain.from_iterable(
                self.courses_by_level(max_level=5000).values())),
            "combined": [],
            "grad exclusive": list(itertools.chain.from_iterable(
                self.courses_by_level(min_level=6000).values()))
            }

        # Not all of the 5000 level courses are combined with graduate
        # level courses, so we must filter out the ones that do.
        undergrads_to_delete = []
        for undergrad_course in by_career["undergrad exclusive"]:
            matching_grad_course = list(filter(lambda course:
                course.name == undergrad_course.name,
                by_career["grad exclusive"]
                ))
            if len(matching_grad_course) > 0:
                undergrads_to_delete.append(undergrad_course)
                by_career["combined"].append(matching_grad_course[0])
                by_career["grad exclusive"].remove(matching_grad_course[0])

        for undergrad_course in undergrads_to_delete:
            by_career["undergrad exclusive"].remove(undergrad_course)

        return by_career

def box_plot_x_ticks(x_data) -> List[float]:
    max_x_tick = 1.0
    while max_x_tick < max(x_data):
        max_x_tick += 0.2
    return list(np.arange(0,max_x_tick+0.2,0.2))

def box_plot(output_name, x_name, x_data, show):
    fig, ax = plt.subplots()
    ax.boxplot(x_data, vert=False)

    ax.set_title(f"{x_name}")
    ax.set_xlabel("Enrollment Ratio in Each Course")
    ax.set_xticks(box_plot_x_ticks(x_data))
    ax.set_yticks([])

    if show:
        plt.show()
    fig.savefig(output_name)
    plt.close()

def bar_plot_y_ticks(y_data) -> List[int]:
    max_y_tick = max(y_data) + 2
    if max_y_tick % 2 != 0:
        max_y_tick + 1
    return list(range(0,max_y_tick,2))

def bar_plot(output_name, x_name, y_name, y_data, tick_label, title, show):
    fig, ax = plt.subplots()
    ax.bar(list(range(len(y_data))), y_data, tick_label=tick_label)

    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    ax.set_yticks(bar_plot_y_ticks(y_data))
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
    catalogs = {}
    with open(data_file) as fin:
        for raw_catalog in json.load(fin):
            catalog = CourseCatalog.from_dict(raw_catalog)
            catalogs[catalog.semester_name] = catalog

    for catalog in catalogs.values():
        catalog.enrollment_plots(show)
        catalog.available_courses_plots(show)

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
