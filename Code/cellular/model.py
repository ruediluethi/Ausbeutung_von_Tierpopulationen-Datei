from random import choice
from xml.etree import ElementTree

from Code.cellular.entity import Entity
from Code.cellular.util import adult_checker


class _Species:
    def __init__(self, xml_objext: ElementTree.Element):
        self._xml = xml_objext
        self.name = xml_objext.get("name")
        maximum_age = xml_objext.find("maximum_age")
        self.maximum_age = int(maximum_age.get("age")) if maximum_age is not None else 0
        reproduction = xml_objext.find("reproduction")
        self.reproduction = float(reproduction.get("r")) if reproduction is not None else 0
        reproduction_age = xml_objext.find("reproduction_age")
        if reproduction_age is not None:
            self.reproduction_age = int(reproduction_age.get("age"))
        else:
            self.reproduction_age = 0
        #print(self.reproduction_age)
    def __str__(self):
        return f"Animal {self.name} with maximum_age {self.maximum_age} and reproduction {self.reproduction}"

    def __copy__(self):
        return _Species(self._xml)
        # def get_Ertrag(self, animals_counter):
        #    animal


class _Cell:
    def __init__(self, xml_object: ElementTree.Element, base):
        self._xml = xml_object
        self.base = base
        self.x = int(xml_object.get("x"))
        self.y = int(xml_object.get("y"))
        self.time = 0
        self._growth = {}
        self._amount = {}
        for species in base.species.keys():
            self._growth.update({species:[]})
            self._amount.update({species:[]})
        l = xml_object.find("limit")
        self.limit = int(l.get("K")) if l is not None else 0

        self.inhabitants = {}
        self.entities = {}
        for animal in xml_object.findall("inhabitant"):
            name = animal.get("name")
            amount = int(animal.get("amount"))
            self.inhabitants.update({name: int(amount)})
            self.entities.update({name:[Entity(self.x, self.y, name, born=-round(base.species[name].maximum_age/amount*n)) for n in range(amount)]})

    def add_entity(self, name: str, amount: int):
        ent = self.entities[name]
        ent += [Entity(self.x, self.y, name, born=self.time) for n in range(amount)]
        self.inhabitants[name] += amount

    def kill_random(self, name: str, amount: int):
        ent = self.entities[name]
        for n in range(amount):
            if ent:
                ent.remove(choice(ent))
        self.inhabitants[name] -= amount

    def kill_old_animals(self):
        for species in self.entities:
            s = self.base.species[species]
            dead_animals = []
            for animal in self.entities[species]:
                if self.time-animal.born > s.maximum_age:
                    dead_animals.append(animal)
            for dead in dead_animals:
                self.entities[species].remove(dead)
            self.inhabitants[species] -= len(dead_animals)

    def toamount(self, name: str, amount: int):
        current = self.inhabitants[name]
        if amount > current:
            self.add_entity(name, amount - current)
        elif amount < current:
            self.kill_random(name, current - amount)

    def tick(self):
        self.time += self.base.delta
        self.kill_old_animals()
        species = "Blauwal"
        species_data = self.base.species[species]
        adult = adult_checker(species_data, self.time)
        n = len(list(filter(adult.is_adult, self.entities[species])))

        change = species_data.reproduction * (1 - n / self.limit) * n
        total_amount = self.inhabitants[species]
        total_amount += round(change*self.base.delta)
        self.toamount(species, total_amount)
        self._growth[species].append(change/self.base.delta)
        self._amount[species].append(total_amount)

    def export(self):
        return self._growth, self._amount

    def __str__(self):
        return f"Cell X={self.x}, Y={self.y} with {len(self.inhabitants)} Species"

    def __copy__(self):
        return _Cell(self._xml, self.base)


class Base:
    def __init__(self, xml_file: str):
        self._xml = ElementTree.parse(xml_file)
        self._root = self._xml.getroot()
        self.duration = self._root.get("duration")
        self.delta = float(self._root.get("delta"))

        self.species = {}
        for species in self._root.findall("species"):
            s = _Species(species)
            self.species.update({s.name: s})

        self.cells = {}
        for cell in self._root.findall("cell"):
            c = _Cell(cell, self)
            self.cells.update({(c.x, c.y): c})


    def tick(self):
        for cell in self.cells.values():
            cell.tick()
