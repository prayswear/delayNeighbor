import logging
import collections

logger = logging.getLogger('nrs')


class LNMRS():
    def __init__(self, pos, level):
        self.pos = pos
        self.level = level
        self.neighbor = []
        self._database = collections.defaultdict(set)
        self.current_load = 0
        self.log = []

    def register(self, eid, na):
        self._database[eid].add(na)

    def deregister(self, eid, na):
        if eid in self._database:
            if na in self._database[eid]:
                self._database[eid].remove(na)

    def resolve(self, eid):
        if eid not in self._database:
            return []
        else:
            return self._database[eid]

    def show_db(self):
        # logger.info(self._database)
        print(self._database)


if __name__ == "__main__":
    gnrs = LNMRS(1, 1)
    gnrs.register(1, 1)
    gnrs.show_db()
    gnrs.register(1, 2)
    gnrs.register(2, 2)
    gnrs.show_db()
    gnrs.deregister(1, 2)
    gnrs.show_db()
    print(gnrs.resolve(1))
