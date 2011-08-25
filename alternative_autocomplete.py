import sublime
import sublime_plugin
import re

def uniq(list):
  seen = set()
  return [value for value in list if value not in seen and not seen.add(value)]

def fuzzy_match(query, word):
  query, word = query.lower(), word.lower()
  qi, wi = 0, 0
  while qi < len(query):
    wi = word.find(query[qi], wi)
    if wi == -1:
      return False
    qi += 1
  return True

class Candidate:
  def __init__(self, distance, text):
    self.distance = distance
    self.text = text

  def __hash__(self):
    return hash(self.text)

  def __cmp__(self, other):
    return cmp(self.text, other.text)

class AlternativeAutocompleteCommand(sublime_plugin.TextCommand):

  candidates = []
  previous_completion = None

  def run(self, edit):
    view = self.view
    self.insert_next_completion(view.sel()[0].b, view.substr(sublime.Region(0, view.size())))

  def insert_next_completion(self, position, text):
    prefix_match = re.search(r'([\w\d_]+)\Z', text[0:position], re.M | re.U)
    if prefix_match:
      prefix = prefix_match.group(1)
      if self.previous_completion is None or prefix != self.previous_completion:
        self.previous_completion = None
        self.candidates = self.find_candidates(prefix, position, text)
      if self.candidates:
        edit = self.view.begin_edit()
        self.view.erase(edit, sublime.Region(prefix_match.start(1), prefix_match.end(1)))
        if self.previous_completion is None:
          completion = self.candidates[0]
        else:
          completion = self.candidates[(self.candidates.index(self.previous_completion) + 1) % len(self.candidates)]
        self.view.insert(edit, prefix_match.start(1), completion)
        self.view.end_edit(edit)
        self.previous_completion = completion

  def find_candidates(self, prefix, position, text):
    candidates = []
    regex = re.compile(r'[^\w\d](' + re.escape(prefix) + r'[\w\d]+)', re.M | re.U)
    for match in regex.finditer(text):
      candidates.append(Candidate(abs(match.start(1) - position), match.group(1)))
      if len(candidates) > 100:
        break
    if candidates:
      candidates.sort(lambda a, b: cmp(a.distance, b.distance))
      candidates = [candidate.text for candidate in candidates]
    else:
      word_regex = re.compile(re.escape(prefix[0:1]) + r'[\w\d]+', re.M | re.U | re.I)
      words = word_regex.findall(text)
      candidates = [word for word in words if word != prefix and fuzzy_match(prefix, word)]
    if candidates:
      candidates.append(prefix)
    return uniq(candidates)
