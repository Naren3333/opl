class ManagedObject:
    def __init__(self):
        self.marked = False

    def children(self):
        return []

    def gc_name(self):
        return type(self).__name__


class GarbageCollector:
    def __init__(self, threshold=64, debug=False):
        self.objects = []
        self.threshold = threshold
        self.debug = debug

    def track(self, obj):
        self.objects.append(obj)
        return obj

    def should_collect(self):
        return len(self.objects) >= self.threshold

    def collect(self, roots):
        before = len(self.objects)

        for root in roots:
            self.mark_value(root)

        survivors = []
        collected = 0

        for obj in self.objects:
            if obj.marked:
                obj.marked = False
                survivors.append(obj)
            else:
                collected += 1
                if self.debug:
                    print(f"[GC] Sweeping unreachable {obj.gc_name()}")

        self.objects = survivors

        if self.debug:
            print(f"[GC] Collected {collected} objects")
            print(f"[GC] Heap size {before} -> {len(self.objects)}")

        return collected

    def mark_value(self, value):
        if isinstance(value, ManagedObject):
            self.mark_object(value)
        elif isinstance(value, list):
            for item in value:
                self.mark_value(item)
        elif isinstance(value, dict):
            for key, item in value.items():
                self.mark_value(key)
                self.mark_value(item)

    def mark_object(self, obj):
        if obj.marked:
            return

        obj.marked = True
        if self.debug:
            print(f"[GC] Marking {obj.gc_name()}")

        for child in obj.children():
            self.mark_value(child)
