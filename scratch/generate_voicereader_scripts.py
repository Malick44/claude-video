#!/usr/bin/env python3
"""
Generate 10 mathematically calibrated 24-second Dylan Page style UGC scripts for VoiceReader App.
Adheres strictly to the dylan_hook_voiceover skill specifications:
- Duration: 24.0s
- Cadence: ~172 WPM (strictly 68-70 words per script)
- 4-Beat Narrative Architecture
- Output files per script: clean_voiceover.txt, voiceover_transcript.txt, transcript.srt, transcript.json
- Plus a consolidated overview markdown file.
"""

import json
from pathlib import Path

TARGET_DURATION = 24.0
TARGET_WPM = 172.0

SCRIPTS = [
    {
        "id": "script_01_adhd_reading_hack",
        "title": "The ADHD Reading Cheat Code",
        "angle": "ADHD & Focus Hack",
        "target_audience": "Students, neurodivergent readers, people struggling with attention spans",
        "hook_archetype": "Urgent Warning / Pattern Interrupt",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "If you have ADHD and can't finish books, stop scrolling.",
                "banner_headline": "ADHD READING SECRET?",
                "visual_action": "Creator leans in close to lens, wide eyes, whispering intensely into microphone."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Introduce central struggle, relatable pain point, and immediate stakes",
                "text": "I used to reread the exact same paragraph ten times in a row before giving up completely.",
                "banner_headline": "REREADING THE SAME LINE...",
                "visual_action": "B-roll cut: Frustrated creator staring blankly at a dense book, facepalming."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "The bizarre turning point, unexpected solution, and demo",
                "text": "Then I imported my entire textbook into VoiceReader, turned on the hyper-realistic narrator at two-times speed, and finished three full chapters while doing my laundry without losing focus once.",
                "banner_headline": "FINISHED 3 CHAPTERS IN 20 MIN!",
                "visual_action": "Phone screen recording showing VoiceReader app: animated karaoke highlight running at 2x speed while creator folds clothes with AirPods in."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Is this a genius productivity hack, or does listening count as actual cheating?",
                "banner_headline": "IS LISTENING CHEATING?",
                "visual_action": "Creator cuts back to front camera, raising an eyebrow with an amused, questioning grin."
            }
        ]
    },
    {
        "id": "script_02_professor_exam_cram",
        "title": "The Professor's Exam Cram Hack",
        "angle": "College & Academic Panic",
        "target_audience": "College students, high schoolers facing finals",
        "hook_archetype": "Controversial Secret / Warning",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "Your professors will genuinely hate me for showing you this secret.",
                "banner_headline": "PROFESSORS WILL HATE THIS!",
                "visual_action": "Creator shakes head at camera, finger pointing at viewer in cautionary stance."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Establish immediate high-stakes crisis",
                "text": "Finals are next week and you still have four hundred pages of mandatory reading left to finish.",
                "banner_headline": "400 PAGES BEFORE EXAMS...",
                "visual_action": "Cut to laptop screen showing massive 70-page syllabus and dense PDF stack."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "The turning point and effortless solution",
                "text": "Drop that nightmare PDF right into VoiceReader App. It literally converts dense academic jargon into a natural podcast voice you can absorb at double speed while driving to campus.",
                "banner_headline": "PDF TO PODCAST IN SECONDS!",
                "visual_action": "Screen capture dragging PDF into VoiceReader: instantly converts into waveforms and crisp, smooth narration."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Would you use this to pass your exams, or stick to all-night cramming?",
                "banner_headline": "CRAM OR LISTEN?",
                "visual_action": "Creator looks straight down lens, tapping chin thoughtfully."
            }
        ]
    },
    {
        "id": "script_03_borderline_illegal_hack",
        "title": "The Borderline Illegal Productivity Hack",
        "angle": "Tech Secrets & Forbidden Shortcuts",
        "target_audience": "Tech enthusiasts, entrepreneurs, productivity geeks",
        "hook_archetype": "Forbidden Knowledge",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "This app feels borderline illegal, but absolutely nobody is talking about it.",
                "banner_headline": "BORDERLINE ILLEGAL APP?",
                "visual_action": "Creator glances left and right as if sharing top secret classified info."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Introduce common universal bottleneck",
                "text": "Everyone complains they don't have enough time to read books or stay on top of industry news.",
                "banner_headline": "NO TIME TO READ?",
                "visual_action": "Quick montage: stack of unread books collecting dust on coffee table."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "Mind-blowing revelation of product capabilities",
                "text": "With VoiceReader, you paste any webpage, document, or e-book, and its AI voices sound so incredibly human that you genuinely forget you're not listening to a professionally produced audiobook.",
                "banner_headline": "SOUNDS LIKE A HUMAN NARRATOR!",
                "visual_action": "Live phone demonstration: pasting an article link, voice kicks in with stunningly realistic human cadence."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Tell me down below: could you replace traditional reading with this completely?",
                "banner_headline": "REPLACE READING FOREVER?",
                "visual_action": "Creator holds hands up in a weighing scale motion."
            }
        ]
    },
    {
        "id": "script_04_300_page_book_challenge",
        "title": "The 300-Page Book in 3 Hours Challenge",
        "angle": "Speed Reading / Quantifiable Benchmark",
        "target_audience": "Avid book readers, self-improvement enthusiasts",
        "hook_archetype": "Unbelievable Feat / Stat Shock",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "I just finished an entire three-hundred page book in one afternoon.",
                "banner_headline": "300 PAGES IN ONE AFTERNOON?",
                "visual_action": "Creator slaps a thick 300-page book onto table, staring into camera in disbelief."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Highlight normal limitations vs benchmark",
                "text": "Most people read at two hundred words per minute, meaning books sit unread on their nightstand.",
                "banner_headline": "UNFINISHED NIGHTSTAND BOOKS...",
                "visual_action": "Creator pans across a nightstand with 5 half-finished books."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "The secret method and dual-sensory retention",
                "text": "I loaded the whole book into VoiceReader, bumped the speed up to two-point-five, and because the synchronized text highlights every spoken word, my retention was actually higher than reading normally.",
                "banner_headline": "2.5X SPEED WITH FULL RETENTION!",
                "visual_action": "Close up on phone screen: speed slider hitting 2.5x, words glowing yellow as voice flies smoothly."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Would you try this speed-reading method, or is it way too fast?",
                "banner_headline": "TOO FAST OR GENIUS?",
                "visual_action": "Creator points down toward comment section with slight smirk."
            }
        ]
    },
    {
        "id": "script_05_physical_book_scanner",
        "title": "The Physical Book Camera Scanner",
        "angle": "Hardware Camera Magic / Instant Gratification",
        "target_audience": "Physical book buyers, students with paper handouts",
        "hook_archetype": "Futuristic Tech Contrast",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "You can literally point your phone camera at physical books now.",
                "banner_headline": "SCAN ANY PHYSICAL BOOK!",
                "visual_action": "Over-the-shoulder shot: Phone camera hovering over open paperback novel."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Everyday scenario where hands are tied",
                "text": "I had this heavy paperback I wanted to read, but my hands were completely busy prepping dinner.",
                "banner_headline": "HANDS FULL IN THE KITCHEN...",
                "visual_action": "Creator chopping vegetables on cutting board with book propped up awkwardly."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "Demonstrating the OCR-to-Audio magic",
                "text": "I snapped one quick photo using VoiceReader App, and in under two seconds, it turned the printed page into crystal-clear speech with zero robotic pauses or awkward mispronunciations.",
                "banner_headline": "PHOTO TO SPEECH IN 2 SECONDS!",
                "visual_action": "Phone snaps photo in app; instant OCR processing banner turns immediately into smooth audio playback."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Are physical books becoming obsolete, or do you still prefer holding paper pages?",
                "banner_headline": "ARE PHYSICAL BOOKS OBSOLETE?",
                "visual_action": "Creator holds paperback in one hand, phone in the other, smiling."
            }
        ]
    },
    {
        "id": "script_06_robot_voice_is_dead",
        "title": "The Robot Voice is Officially Dead",
        "angle": "Tech Revolution / AI Voice Quality",
        "target_audience": "Tech skeptics, audiobook listeners, casual scrollers",
        "hook_archetype": "Bold Definitive Statement",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "Throw away everything you thought you ever knew about text-to-speech.",
                "banner_headline": "ROBOT VOICES ARE DEAD!",
                "visual_action": "Creator waves hand dismissively, intensely leaning towards camera."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Trigger nostalgia and shared frustration",
                "text": "Remember those awful, stiff GPS voices from ten years ago that gave you an instant headache?",
                "banner_headline": "THAT OLD STIFF GPS VOICE...",
                "visual_action": "Imitates monotone robotic voice while clutching temples in mock pain."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "Auditory contrast & demonstration of realism",
                "text": "VoiceReader just rolled out ultra-natural AI narrators that breathe, pause for dramatic effect, and emphasize key emotional words so realistically that audio producers literally cannot tell the difference.",
                "banner_headline": "BREATHES & PAUSES NATURALLY!",
                "visual_action": "VoiceReader voice picker UI showing expressive voice personas, audio waveform pulsing dynamically."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Listen closely for yourself and tell me down below: can you spot the AI voice?",
                "banner_headline": "CAN YOU SPOT THE AI?",
                "visual_action": "Creator cups hand to ear with a challenging smile."
            }
        ]
    },
    {
        "id": "script_07_severe_screen_fatigue",
        "title": "The Severe Screen Fatigue Fix",
        "angle": "Health, Wellness & Eye Relief",
        "target_audience": "Office workers, developers, late-night readers, students",
        "hook_archetype": "Health Warning / Pain Point",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "If staring at screens all day gives you migraines, watch this right now.",
                "banner_headline": "FIX SEVERE SCREEN FATIGUE!",
                "visual_action": "Creator rubbing tired eyes under harsh fluorescent desk lamp."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Relatable end-of-workday fatigue scenario",
                "text": "By five PM my eyes were burning, but I still had thirty pages of contracts to review.",
                "banner_headline": "BURNING EYES AT 5 PM...",
                "visual_action": "POV shot of glaring 4K monitor filled with tiny 10pt black-and-white text."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "The restorative relief mechanism",
                "text": "Instead of ruining my vision, I opened VoiceReader, plugged in my AirPods, closed my eyes, and effortlessly soaked up every single detail while reclining in the dark.",
                "banner_headline": "CLOSE YOUR EYES & LISTEN!",
                "visual_action": "Creator taps AirPod into ear, slumps comfortably into couch, eyes peacefully closed."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Would you rather read with your eyes, or listen like this every day?",
                "banner_headline": "EYES OR AIRPODS?",
                "visual_action": "Creator opens one eye, smiling relaxed at camera."
            }
        ]
    },
    {
        "id": "script_08_commute_time_machine",
        "title": "The Commute & Gym Time Machine",
        "angle": "Habit Stacking & Time Mastery",
        "target_audience": "Daily commuters, drivers, fitness goers",
        "hook_archetype": "Time Waste Call-Out",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "Stop wasting forty minutes every morning sitting in heavy rush hour traffic.",
                "banner_headline": "WASTING 40 MIN IN TRAFFIC?",
                "visual_action": "Creator sitting in car driver seat (parked), hands gesturing in frustration at windshield."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Identify lost time that yields zero return",
                "text": "Most people listen to the exact same radio songs every commute and learn absolutely nothing new.",
                "banner_headline": "SAME BORING RADIO SONGS...",
                "visual_action": "Finger repeatedly hitting radio skip buttons on dashboard."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "Transforming dead time into massive compounding knowledge",
                "text": "I queued all my work articles and personal reading into VoiceReader. Now my daily drive turns into a private masterclass, and I finish a full book every single week.",
                "banner_headline": "FINISH A BOOK EVERY WEEK!",
                "visual_action": "Phone mounted on dashboard connected via Bluetooth playing VoiceReader with clean CarPlay-friendly interface."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "What are you listening to during your commute right now? Comment below.",
                "banner_headline": "WHAT DO YOU LISTEN TO?",
                "visual_action": "Creator points down toward center console/comments."
            }
        ]
    },
    {
        "id": "script_09_lazy_student_secret",
        "title": "The Lazy Student's 4.0 GPA Secret",
        "angle": "Unfair Advantage / High Grades",
        "target_audience": "High school & university students wanting top marks with minimal effort",
        "hook_archetype": "Envy / Mystery Revelation",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "How the laziest guy in our entire class got straight A's effortlessly.",
                "banner_headline": "LAZY GUY GOT STRAIGHT A'S?",
                "visual_action": "Creator leans in conspiratorially, talking low and fast."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Contrast traditional hard study with effortless results",
                "text": "He never touched a physical highlighter or opened a single dense textbook during study hall.",
                "banner_headline": "NEVER TOUCHED A TEXTBOOK...",
                "visual_action": "Pans past fellow students hunched over books with 6 different highlighters."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "The auditory hacking loop",
                "text": "His secret was scanning lecture slides and syllabi into VoiceReader, putting it on double speed while playing video games, and letting his auditory memory absorb all the exam material automatically.",
                "banner_headline": "GAMING WHILE STUDYING!",
                "visual_action": "Split screen: gaming on console while VoiceReader plays synchronized study notes in background."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Is this pure academic genius, or is it completely unfair to everyone?",
                "banner_headline": "GENIUS OR UNFAIR?",
                "visual_action": "Creator shrugs with a smirk: 'you decide'."
            }
        ]
    },
    {
        "id": "script_10_dyslexia_reading_miracle",
        "title": "The Dyslexia & Struggling Reader Miracle",
        "angle": "Accessibility & Dual-Modality Learning",
        "target_audience": "Dyslexic readers, ESL learners, slow reading adults",
        "hook_archetype": "Emotional & Transformational Hook",
        "beats": [
            {
                "beat_id": "01_hook",
                "name": "The Scroll-Stop Hook",
                "start_time": 0.0,
                "end_time": 3.2,
                "duration": 3.2,
                "inflection": "[Intense Whisper / Shocked Eye Contact / Sudden Peak]",
                "tone": "intense whisper with shocked emphasis",
                "role": "Pattern Interrupt - Stop Mindless Scrolling",
                "text": "This might actually be the most life-changing accessibility app ever created.",
                "banner_headline": "MOST LIFE-CHANGING APP?",
                "visual_action": "Creator looks sincerely and directly into camera with genuine awe."
            },
            {
                "beat_id": "02_setup",
                "name": "The Setup & Entities",
                "start_time": 3.2,
                "end_time": 8.8,
                "duration": 5.6,
                "inflection": "[Rapid-fire Matter-of-Fact Delivery / Fast Tempo]",
                "tone": "rapid-fire matter-of-fact delivery and fast tempo",
                "role": "Address real, painful struggles with text processing",
                "text": "If you struggle with dyslexia, words literally scramble across the screen and make reading agonizingly slow.",
                "banner_headline": "WORDS SCRAMBLING ON SCREEN...",
                "visual_action": "Visual effect showing words blurring slightly on a page to illustrate dyslexia struggle."
            },
            {
                "beat_id": "03_escalation_twist",
                "name": "The Dramatic Twist",
                "start_time": 8.8,
                "end_time": 19.5,
                "duration": 10.7,
                "inflection": "[Incredulous Pause / Pitch Shift / Shocked Delivery]",
                "tone": "incredulous and shocked with building excitement",
                "role": "Dual-sensory solution that unlocks fluid reading",
                "text": "VoiceReader uses dual modality sensory learning, highlighting every word in bright dynamic color while reading aloud with studio quality AI voices, completely eliminating reading fatigue for good.",
                "banner_headline": "ELIMINATES READING FATIGUE!",
                "visual_action": "Crisp close-up on VoiceReader's live karaoke-style word highlighter in action, paired with a warm, natural human voice."
            },
            {
                "beat_id": "04_outro_question",
                "name": "The Moral Dilemma & Question",
                "start_time": 19.5,
                "end_time": 24.0,
                "duration": 4.5,
                "inflection": "[Deadpan Delivery / Eyebrow Raise / Direct Gaze]",
                "tone": "amused deadpan and engaging rising intonation",
                "role": "Viral Engagement Engine: prompt debate in comments",
                "text": "Share this with someone who struggles with reading, and tell me your personal thoughts below.",
                "banner_headline": "SHARE WITH A FRIEND!",
                "visual_action": "Creator gestures with hands, warm inviting smile."
            }
        ]
    }
]

def format_srt_timestamp(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_readable_transcript(item: dict) -> str:
    beats = item["beats"]
    total_words = sum(len(b["text"].split()) for b in beats)
    cadence = round((total_words / TARGET_DURATION) * 60, 1)

    lines = []
    lines.append("=" * 75)
    lines.append(f"VOICEREADER UGC SCRIPT: {item['title'].upper()} ({TARGET_DURATION}s)")
    lines.append(f"Angle: {item['angle']} | Target Audience: {item['target_audience']}")
    lines.append(f"Pacing: {cadence} WPM (Target: 172 WPM) | Total Spoken Words: {total_words}")
    lines.append("=" * 75)
    lines.append("")

    for b in beats:
        lines.append(f"[{b['start_time']:04.1f}s - {b['end_time']:04.1f}s] {b['name'].upper()} ({len(b['text'].split())} words)")
        lines.append(f"Banner Headline: {b['banner_headline']}")
        lines.append(f"Vocal Tone:      {b['tone']}")
        lines.append(f"Inflection Cue:  {b['inflection']}")
        lines.append(f"Visual Action:   {b['visual_action']}")
        lines.append(f"Spoken Voiceover: \"{b['text']}\"")
        lines.append("")

    lines.append("=" * 75)
    lines.append("CLEAN SPOKEN TEXT ONLY (For TTS / AuK-Voice / ElevenLabs):")
    lines.append("=" * 75)
    lines.append(" ".join(b["text"] for b in beats))
    lines.append("")
    return "\n".join(lines)

def format_srt(beats: list) -> str:
    lines = []
    for i, b in enumerate(beats, 1):
        s_str = format_srt_timestamp(b["start_time"])
        e_str = format_srt_timestamp(b["end_time"])
        lines.append(f"{i}")
        lines.append(f"{s_str} --> {e_str}")
        lines.append(b["text"])
        lines.append("")
    return "\n".join(lines)

def main():
    base_out = Path("/Users/malickdes/AIWORKSPACE/claude-video/outputs/voicereader_ugc_scripts")
    base_out.mkdir(parents=True, exist_ok=True)

    summary_rows = []

    # Clean old folders if present
    for p in base_out.iterdir():
        if p.is_dir() and p.name.startswith("0"):
            import shutil
            shutil.rmtree(p)

    for idx, item in enumerate(SCRIPTS, 1):
        clean_id = item['id'].replace('script_', '').replace(f'{idx:02d}_', '')
        folder_name = f"{idx:02d}_{clean_id}"
        script_dir = base_out / folder_name
        script_dir.mkdir(parents=True, exist_ok=True)

        beats = item["beats"]
        total_words = sum(len(b["text"].split()) for b in beats)
        cadence = round((total_words / TARGET_DURATION) * 60, 1)

        manifest = {
            "id": item["id"],
            "title": item["title"],
            "angle": item["angle"],
            "target_audience": item["target_audience"],
            "target_duration_sec": TARGET_DURATION,
            "total_words": total_words,
            "cadence_wpm": cadence,
            "target_wpm_baseline": TARGET_WPM,
            "beats": beats
        }

        # 1. Clean voiceover
        clean_text = " ".join(b["text"] for b in beats)
        (script_dir / "clean_voiceover.txt").write_text(clean_text, encoding="utf-8")

        # 2. Readable transcript
        readable_text = format_readable_transcript(item)
        (script_dir / "voiceover_transcript.txt").write_text(readable_text, encoding="utf-8")

        # 3. Subtitles SRT
        srt_text = format_srt(beats)
        (script_dir / "transcript.srt").write_text(srt_text, encoding="utf-8")

        # 4. JSON manifest
        (script_dir / "transcript.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        summary_rows.append((idx, item["title"], item["angle"], total_words, cadence, item['beats'][0]['banner_headline']))
        print(f"[{idx:02d}/10] Generated: {item['title']} -> {total_words} words ({cadence} WPM)")

    # Write Master README
    readme_lines = [
        "# VoiceReader App — 10 High-Retention 24-Second UGC Scripts",
        "",
        "Engineered with **Dylan Page's Empirical 4-Beat Short-Form Retention Formula**.",
        "",
        "## Performance Metrics",
        "- **Target Duration:** Exactly 24.0 seconds",
        "- **Target Pacing:** 168–175 Words Per Minute (Average: 172 WPM)",
        "- **Word Count Range:** 68–70 words strictly calibrated for high-speed engagement without slurring",
        "",
        "## The 4-Beat Narrative Architecture",
        "1. **Beat 1: Scroll-Stop Hook (0.0s – 3.2s)** — Pattern interrupt with intense vocal inflection (`8–11 words`)",
        "2. **Beat 2: Relatable Crisis / Setup (3.2s – 8.8s)** — Immediate stakes and entity establishment (`16–18 words`)",
        "3. **Beat 3: Escalation & App Demo Twist (8.8s – 19.5s)** — The 'aha!' moment and speed/sensory demo (`28–30 words`)",
        "4. **Beat 4: Viral Comment Bait / Outro (19.5s – 24.0s)** — Polarizing dilemma driving comments (`11–13 words`)",
        "",
        "## Script Roster Overview",
        "",
        "| # | Script Title | Angle / Hook Type | Words | WPM | Lead Banner Headline |",
        "|---|---|---|---|---|---|"
    ]

    for idx, title, angle, words, wpm, banner in summary_rows:
        readme_lines.append(f"| {idx:02d} | **{title}** | {angle} | {words} | {wpm} | `{banner}` |")

    readme_lines.append("")
    readme_lines.append("## Production Pipeline Handoff")
    readme_lines.append("Each script subfolder contains:")
    readme_lines.append("- `clean_voiceover.txt` — Pure spoken text ready for TTS / AuK-Voice / ElevenLabs")
    readme_lines.append("- `voiceover_transcript.txt` — Human-readable script with timestamps, vocal tones, and visual UGC directions")
    readme_lines.append("- `transcript.srt` — Timed SubRip subtitles for CapCut / Premiere")
    readme_lines.append("- `transcript.json` — Structured manifest for automated audio cloning pipelines")
    readme_lines.append("")

    (base_out / "README.md").write_text("\n".join(readme_lines), encoding="utf-8")
    print(f"\n[+] Master index saved to {base_out / 'README.md'}")

if __name__ == "__main__":
    main()
