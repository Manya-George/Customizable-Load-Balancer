import bisect

class ConsistentHashMap:
    def __init__(self, num_slots=512, num_virtuals=9):
        self.num_slots = num_slots
        self.num_virtuals = num_virtuals
        self.hash_ring = {}       # slot -> server_id
        self.sorted_keys = []     # sorted list of slot hashes
        self.servers = set()

    def _hash_virtual(self, server_id, virtual_id):
        return (server_id + virtual_id + (2 ** virtual_id) + 25) % self.num_slots

    def _hash_request(self, key: int):
        return (key + (2 ** key) + 17) % self.num_slots

    def add_server(self, server_id):
        if server_id in self.servers:
            return
        self.servers.add(server_id)
        for v in range(self.num_virtuals):
            h = self._hash_virtual(server_id, v)
            while h in self.hash_ring:
                h = (h + 1) % self.num_slots
            self.hash_ring[h] = server_id
            bisect.insort(self.sorted_keys, h)

    def remove_server(self, server_id):
        if server_id not in self.servers:
            return
        self.servers.remove(server_id)
        to_remove = [h for h, s in self.hash_ring.items() if s == server_id]
        for h in to_remove:
            del self.hash_ring[h]
            self.sorted_keys.remove(h)

    def get_server(self, request_key: int):
        h = self._hash_request(request_key)
        idx = bisect.bisect_right(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0
        return self.hash_ring[self.sorted_keys[idx]]
