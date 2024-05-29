import miditoolkit
import json

##############################
# constants
##############################
DEFAULT_BEAT_RESOL = 480
DEFAULT_BAR_RESOL = 480 * 4
DEFAULT_FRACTION = 16


##############################
# containers for conversion
##############################
class ConversionEvent(object):
  def __init__(self, event, is_full_event=False):
    if not is_full_event:
      if 'Note' in event or 'Phrase_Tag' in event:
        self.name, self.value = '_'.join(event.split('_')[:-1]), event.split('_')[-1]
      elif 'Chord' in event:
        self.name, self.value = event.split('_')[0], '_'.join(event.split('_')[1:])
      elif 'New_Beat' in event:
        self.name, self.value = '_'.join(event.split('_')[:2]), event.split('_')[2]
      elif len(event.split('_')) == 2:
        self.name, self.value = event.split('_')
      else:
        self.name, self.value = '_'.join(event.split('_')[:-1]), event.split('_')[-1]
    else:
      self.name, self.value = event['name'], event['value']
  def __repr__(self):
    return 'Event(name: {} | value: {})'.format(self.name, self.value)

class NoteEvent(object):
  def __init__(self, pitch, bar, position, duration, velocity):
    self.pitch = pitch
    self.start_tick = bar * DEFAULT_BAR_RESOL + position * (DEFAULT_BAR_RESOL // DEFAULT_FRACTION)
    self.duration = duration
    self.velocity = velocity
  
class TempoEvent(object):
  def __init__(self, tempo, bar, position):
    self.tempo = tempo
    self.start_tick = bar * DEFAULT_BAR_RESOL + position * (DEFAULT_BAR_RESOL // DEFAULT_FRACTION)

class ChordEvent(object):
  def __init__(self, chord_val, bar, position):
    self.chord_val = chord_val
    self.start_tick = bar * DEFAULT_BAR_RESOL + position * (DEFAULT_BAR_RESOL // DEFAULT_FRACTION)
  def __repr__(self):
    return '[ {} at {} ]'.format(self.chord_val, self.start_tick)

##############################
# conversion functions
##############################
def read_generated_txt(generated_path):
  f = open(generated_path, 'r')
  return f.read().splitlines()


def skyline_event_to_midi(events, output_midi_path=None, is_full_event=False, 
                          enforce_tempo=False, enforce_tempo_val=None, return_tempo=False, add_basic_chord=False):
  
  # Specify the file path of the JSON file
  json_file_path = 'stage01_compose/chord_templates.json'
  # Read the dictionary from the JSON file
  with open(json_file_path, 'r') as json_file:
      CHORD_NOTES_MAP = json.load(json_file)

  events = [ConversionEvent(ev, is_full_event=is_full_event) for ev in events]
  # print (events[:20])

  # assert events[0].name == 'Bar'
  temp_notes = []
  temp_tempos = []
  temp_chords = []
  temp_phrases = []

  cur_bar = -1
  cur_position = 0

  for i in range(len(events)):
    if events[i].name == 'Bar':
      if i > 0:
        cur_bar += 1
    elif events[i].name == 'Beat':
      cur_position = int(events[i].value)
      assert cur_position >= 0 and cur_position < DEFAULT_FRACTION
    elif events[i].name == 'Tempo':
      temp_tempos.append(TempoEvent(
        int(events[i].value), max(cur_bar, 0), cur_position
      ))
    elif 'Note_Pitch' in events[i].name and \
         (i+1) < len(events) and 'Note_Duration' in events[i+1].name:
      # check if the 3 events are of the same instrument
      temp_notes.append(
        NoteEvent(
          pitch=int(events[i].value), 
          bar=cur_bar, position=cur_position, 
          duration=int(events[i+1].value), velocity=80
        )
      )
    elif 'Chord' in events[i].name:
      temp_chords.append(
        ChordEvent(events[i].value, cur_bar, cur_position)
      )
    elif 'Phrase_Tag' in events[i].name:
      temp_phrases.append(
        ChordEvent(events[i].value, cur_bar, 0)
      )
    elif events[i].name in ['EOS', 'PAD']:
      continue

  # print (len(temp_tempos), len(temp_notes))
  # print (temp_phrases)

  midi_obj = miditoolkit.midi.parser.MidiFile()
  if add_basic_chord:
    midi_obj.instruments = [
      miditoolkit.Instrument(program=0, is_drum=False, name='Piano'),
      miditoolkit.Instrument(program=0, is_drum=False, name='Piano')
    ]
  else:
    midi_obj.instruments = [
      miditoolkit.Instrument(program=0, is_drum=False, name='Piano')
    ]

  for n in temp_notes:
    midi_obj.instruments[0].notes.append(
      miditoolkit.Note(int(n.velocity), n.pitch, int(n.start_tick), int(n.start_tick + n.duration))
    )
  for b in range(cur_bar):
    midi_obj.markers.append(
      miditoolkit.Marker('Bar-{}'.format(b+1), int(DEFAULT_BAR_RESOL * b))
    )

  pre_save_start_tick = []
  for c in temp_chords:
    midi_obj.markers.append(
      miditoolkit.Marker('Chord-{}'.format(c.chord_val), int(c.start_tick))
    )
    if c.chord_val == "N_N":
      continue
    pre_save_start_tick.append(c.start_tick)
  
  # assert len(pre_save_start_tick) == len(temp_chords)
  if add_basic_chord:
    for i, c in enumerate(temp_chords):
      if c.chord_val == "N_N":
        continue
      chord_notes = CHORD_NOTES_MAP[c.chord_val]
      # print(c.chord_val, CHORD_NOTES_MAP[c.chord_val])
      # print(len(temp_chords))
      for note in chord_notes:
        if i==(len(temp_chords)-1):
          chord_note = miditoolkit.Note(
              velocity=60,         # Note velocity
              pitch=note,  # Note pitch
              start=c.start_tick,  # Start time in ticks
              end=c.start_tick+480     # End time in ticks
          )
        else:
          chord_note = miditoolkit.Note(
              velocity=60,         # Note velocity
              pitch=note,  # Note pitch
              start=c.start_tick,  # Start time in ticks
              end=pre_save_start_tick[i+1]     # End time in ticks
          )
        midi_obj.instruments[1].notes.append(chord_note)

    #   c.start_tick
  for ph in temp_phrases:
    midi_obj.markers.append(
      miditoolkit.Marker('Phrase-{}'.format(ph.chord_val), int(ph.start_tick))
    )

  if enforce_tempo is False:
    for t in temp_tempos:
      midi_obj.tempo_changes.append(
        miditoolkit.TempoChange(t.tempo, int(t.start_tick))
      )
  else:
    if enforce_tempo_val is None:
      enforce_tempo_val = temp_tempos[1]
    for t in enforce_tempo_val:
      midi_obj.tempo_changes.append(
        miditoolkit.TempoChange(t.tempo, int(t.start_tick))
      )

  if output_midi_path is not None:
    midi_obj.dump(output_midi_path)

  if not return_tempo:
    return midi_obj
  else:
    return midi_obj, temp_tempos


