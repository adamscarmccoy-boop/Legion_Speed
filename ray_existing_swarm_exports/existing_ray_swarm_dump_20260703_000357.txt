# Existing Ray Swarm Dump

- Created: `2026-07-03T00:03:54`
- Ray address: `auto`
- Namespace: `legion`
- Registry: `SwarmKnowledgeRegistry`

## Connection
- `ray_import`: `ok`
- `ray_init`: `ok`
- `runtime_namespace`: `legion`

## Ray State API Actors
State API unavailable: `RayStateApiException: API server internal error. See dashboard.log file for more details. Error: The given filter column namespace is not supported. Enter filters with –-filter key=value or –-filter key!=value Supported filter columns: {'placement_group_id', 'actor_id', 'ray_namespace', 'repr_name', 'job_id', 'class_name', 'name', 'node_id', 'state', 'pid'}`

## Registry
- Found: `True`

## Registry Methods
- `summary`: ok=`True` method=`get_registered_tables_summary`
- `list_tables`: ok=`False` method=`None`
  - errors: `[{'method': 'list_tables', 'error': "AttributeError: 'ActorHandle' object has no attribute 'list_tables'"}, {'method': 'table_names', 'error': "AttributeError: 'ActorHandle' object has no attribute 'table_names'"}, {'method': 'get_table_names', 'error': "AttributeError: 'ActorHandle' object has no attribute 'get_table_names'"}, {'method': 'keys', 'error': "AttributeError: 'ActorHandle' object has no attribute 'keys'"}]`

## Tables
Found/checked `27` table(s).

### `audio_manifest_vectors`
- Rows: `500`
- Columns: `4`
- Column names:
  - `vector`
  - `text`
  - `metadata`
  - `type`
- Preview:
```json
[
  {
    "vector": "[Vector dimension: 768]",
    "text": "Audio:  Claps & Snaps(03) - A#m - 128-1.wav. Path: C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\ Claps & Snaps(03) - A#m - 128-1.wav. Ext: .wav",
    "metadata": "{\"Filename\":\" Claps & Snaps(03) - A#m - 128-1.wav\",\"Drive\":\"C\",\"Extension\":\".wav\",\"Full_Path\":\"C:\\\\Users\\\\adams\\\\MusicSandbox\\\\Categorized_Audio\\\\ Claps & Snaps(03) - A#m - 128-1.wav\"}",
    "type": "audio_asset"
  },
  {
    "vector": "[Vector dimension: 768]",
    "text": "Audio:  Claps & Snaps(03) - A#m - 128.wav. Path: C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\ Claps & Snaps(03) - A#m - 128.wav. Ext: .wav",
    "metadata": "{\"Filename\":\" Claps & Snaps(03) - A#m - 128.wav\",\"Drive\":\"C\",\"Extension\":\".wav\",\"Full_Path\":\"C:\\\\Users\\\\adams\\\\MusicSandbox\\\\Categorized_Audio\\\\ Claps & Snaps(03) - A#m - 128.wav\"}",
    "type": "audio_asset"
  }
]
```

### `audio_vibe_gpu`
- Rows: `1013`
- Columns: `3`
- Column names:
  - `id`
  - `filename`
  - `vector`
- Preview:
```json
[
  {
    "id": "72b2d3dbedb5c8dfa8d3112aa198e6e2a001df003ed9dc39082d275c27ed0742",
    "filename": "KILLA",
    "vector": "[Vector dimension: 384]"
  },
  {
    "id": "12dd2d52526f9b8c0c0821adc9378eaa168b3ddf8d79b702bbdaabc401f22493",
    "filename": "WATCH ME",
    "vector": "[Vector dimension: 384]"
  }
]
```

### `chrislake_stems_duckdb`
- Rows: `4`
- Columns: `13`
- Column names:
  - `filepath`
  - `filename`
  - `asset_type`
  - `drum_type`
  - `tempo`
  - `key`
  - `rms_db`
  - `crest_factor`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
  - `spectral_centroid`
- Preview:
```json
[
  {
    "filepath": "C:\\STUDIES_BACKUP\\separated_stems\\htdemucs\\90. Chris Lake, Gotye, Fisher, Kimbra, Sante Sansone - Somebody (2024) (2024)\\bass.wav",
    "filename": "bass.wav",
    "asset_type": "STEM",
    "drum_type": "BASS",
    "tempo": null,
    "key": null,
    "rms_db": -37.98942947387695,
    "crest_factor": 1.1721795797348022,
    "sub_bass_energy": 3044.17578125,
    "bass_energy": 75.03480529785156,
    "mid_energy": 231.44833374023438,
    "high_energy": 618.223388671875,
    "spectral_centroid": 592.9598170212
  },
  {
    "filepath": "C:\\STUDIES_BACKUP\\separated_stems\\htdemucs\\90. Chris Lake, Gotye, Fisher, Kimbra, Sante Sansone - Somebody (2024) (2024)\\drums.wav",
    "filename": "drums.wav",
    "asset_type": "STEM",
    "drum_type": "DRUMS",
    "tempo": null,
    "key": null,
    "rms_db": -14.412613868713379,
    "crest_factor": 4.225632190704346,
    "sub_bass_energy": 37174.75,
    "bass_energy": 104861.75,
    "mid_energy": 44429.3203125,
    "high_energy": 199412.53125,
    "spectral_centroid": 3335.7380176041984
  }
]
```

### `chris_lake_fused_raw`
- Rows: `65`
- Columns: `21`
- Column names:
  - `track_name`
  - `apple_artist`
  - `apple_genre`
  - `apple_release_date`
  - `audio_filepath`
  - `audio_tempo`
  - `audio_key`
  - `dsp_rms`
  - `dsp_crest`
  - `dsp_sub`
  - `dsp_bass`
  - `dsp_mid`
  - `dsp_high`
  - `dsp_centroid`
  - `spotify_streams`
  - `spotify_chart_position`
  - `lb_listens`
  - `lb_listeners`
  - `lb_trending`
  - `discogs_genre`
  - `discogs_style`
- Preview:
```json
[
  {
    "track_name": "I Want You",
    "apple_artist": "Chris Lake",
    "apple_genre": "Electronic",
    "apple_release_date": "2017-03-22T12:00:00Z",
    "audio_filepath": "E:\\music\\HOUSE\\Traxsource Top 200 Tech House of 2025 - djsoundtop.com\\Rue Jay - I Want Your Love (Extended Mix) - www.djsoundtop.com.mp3",
    "audio_tempo": 129.19921875,
    "audio_key": "G#",
    "dsp_rms": -10.6583051682,
    "dsp_crest": 3.3707630634,
    "dsp_sub": 40.4556846619,
    "dsp_bass": 11.0396432877,
    "dsp_mid": 2.4147808552,
    "dsp_high": 1.254643321,
    "dsp_centroid": 3281.7622070312,
    "spotify_streams": null,
    "spotify_chart_position": null,
    "lb_listens": null,
    "lb_listeners": null,
    "lb_trending": null,
    "discogs_genre": "Electronic",
    "discogs_style": "House"
  },
  {
    "track_name": "Ease My Mind",
    "apple_artist": "Chris Lake & Abel Balder",
    "apple_genre": "House",
    "apple_release_date": "2025-02-14T12:00:00Z",
    "audio_filepath": "E:\\music\\HOUSE\\Beatport Tech House Top 100 December 2025 - electronicfresh.com\\80. Chris Lake, Odd Mob, Abel Balder - Ease My Mind (Odd Mob Extended Remix).mp3",
    "audio_tempo": 129.19921875,
    "audio_key": "F#",
    "dsp_rms": -8.6265411377,
    "dsp_crest": 2.828622818,
    "dsp_sub": 49.4933166504,
    "dsp_bass": 29.6843528748,
    "dsp_mid": 4.0192580223,
    "dsp_high": 1.4931192398,
    "dsp_centroid": 2570.3505859375,
    "spotify_streams": null,
    "spotify_chart_position": null,
    "lb_listens": null,
    "lb_listeners": null,
    "lb_trending": null,
    "discogs_genre": null,
    "discogs_style": null
  }
]
```

### `chris_lake_omni_baseline`
- Rows: `22`
- Columns: `15`
- Column names:
  - `segment_name`
  - `rms`
  - `crest_factor`
  - `zero_crossing_rate`
  - `spectral_centroid`
  - `spectral_bandwidth`
  - `spectral_rolloff`
  - `spectral_flatness`
  - `spectral_contrast`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
  - `mfcc_vector`
  - `chroma_vector`
- Preview:
```json
[
  {
    "segment_name": "Breakdown / Low Energy 1",
    "rms": 0.2997755706310272,
    "crest_factor": 3.457146644592285,
    "zero_crossing_rate": 0.0666595901268116,
    "spectral_centroid": 3486.9481160061837,
    "spectral_bandwidth": 3720.1652136108582,
    "spectral_rolloff": 6870.90183423913,
    "spectral_flatness": 0.005327092949301004,
    "spectral_contrast": 20.30692400331359,
    "sub_bass_energy": 1476932.5,
    "bass_energy": 21132804.0,
    "mid_energy": 530291.5625,
    "high_energy": 1339453.75,
    "mfcc_vector": "[-255.53419494628906, 66.42169952392578, 11.412667274475098, 48.09184265136719, 10.47428035736084, 28.522371292114258, 8.187382698059082, 19.753711700439453, 4.580677509307861, 12.621682167053223, 6.0544257164001465, 13.084715843200684, 11.576028823852539]",
    "chroma_vector": "[0.6968844532966614, 0.7537961006164551, 0.7928066253662109, 0.7301794290542603, 0.6621922850608826, 0.6384111046791077, 0.5861448645591736, 0.542447566986084, 0.5392688512802124, 0.5668041110038757, 0.5847247838973999, 0.6283187866210938]"
  },
  {
    "segment_name": "Build / Mid Energy 2",
    "rms": 0.3140191435813904,
    "crest_factor": 3.2917706966400146,
    "zero_crossing_rate": 0.056354732789855075,
    "spectral_centroid": 3259.783423896198,
    "spectral_bandwidth": 3635.2483084793216,
    "spectral_rolloff": 6478.435801630435,
    "spectral_flatness": 0.004393792245537043,
    "spectral_contrast": 20.32079056228308,
    "sub_bass_energy": 1531447.25,
    "bass_energy": 23617998.0,
    "mid_energy": 622071.25,
    "high_energy": 1374157.75,
    "mfcc_vector": "[-252.97361755371094, 71.4475326538086, 9.087879180908203, 46.57069396972656, 11.391951560974121, 28.773462295532227, 9.78046703338623, 20.52554702758789, 5.75205135345459, 13.511229515075684, 6.928637504577637, 13.892988204956055, 11.922707557678223]",
    "chroma_vector": "[0.7025281190872192, 0.7548004388809204, 0.7900252342224121, 0.7361677289009094, 0.6768510937690735, 0.6477946639060974, 0.5896821618080139, 0.5483023524284363, 0.5443083047866821, 0.5667561292648315, 0.5920461416244507, 0.6350862383842468]"
  }
]
```

### `chris_lake_raw_features`
- Rows: `9`
- Columns: `46`
- Column names:
  - `filepath`
  - `filename`
  - `asset_type`
  - `drum_type`
  - `tempo`
  - `key`
  - `rms_db`
  - `crest_factor`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
  - `spectral_centroid`
  - `spectral_rolloff`
  - `spectral_bandwidth`
  - `spectral_contrast`
  - `zcr`
  - `onset_strength`
  - `transient_density`
  - `harmonic_ratio`
  - `percussive_ratio`
  - `mfcc_1`
  - `mfcc_2`
  - `mfcc_3`
  - `mfcc_4`
  - `mfcc_5`
  - `mfcc_6`
  - `mfcc_7`
  - `mfcc_8`
  - `mfcc_9`
  - `mfcc_10`
  - `mfcc_11`
  - `mfcc_12`
  - `mfcc_13`
  - `chroma_C`
  - `chroma_Cs`
  - `chroma_D`
  - `chroma_Ds`
  - `chroma_E`
  - `chroma_F`
  - `chroma_Fs`
  - `chroma_G`
  - `chroma_Gs`
  - `chroma_A`
  - `chroma_As`
  - `chroma_B`
- Preview:
```json
[
  {
    "filepath": "E:\\music\\HOUSE\\Beatport Tech House Top 100 December 2025 - electronicfresh.com\\37. Chris Lake, Ragie Ban - Toxic (Extended Mix).mp3",
    "filename": "37. Chris Lake, Ragie Ban - Toxic (Extended Mix).mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 129.19921875,
    "key": "F",
    "rms_db": -11.4126462936,
    "crest_factor": 4.0066623688,
    "sub_bass_energy": 36.4854927063,
    "bass_energy": 17.7685832977,
    "mid_energy": 2.8859257698,
    "high_energy": 1.1437746286,
    "spectral_centroid": 2689.21484375,
    "spectral_rolloff": 5378.2924804688,
    "spectral_bandwidth": 2554.6000976562,
    "spectral_contrast": 20.9711360931,
    "zcr": 0.1253522336,
    "onset_strength": 2.6149048805,
    "transient_density": 4.0555553436,
    "harmonic_ratio": 0.7325931787,
    "percussive_ratio": 0.343724072,
    "mfcc_1": -143.726348877,
    "mfcc_2": 60.9431495667,
    "mfcc_3": 45.4553260803,
    "mfcc_4": 45.664150238,
    "mfcc_5": 15.3579568863,
    "mfcc_6": 18.2758769989,
    "mfcc_7": -0.7052481771,
    "mfcc_8": 4.1208972931,
    "mfcc_9": -4.6181821823,
    "mfcc_10": 1.1208533049,
    "mfcc_11": -2.2726867199,
    "mfcc_12": 0.3184158802,
    "mfcc_13": -3.2405347824,
    "chroma_C": 0.4509708285,
    "chroma_Cs": 0.4669589102,
    "chroma_D": 0.4959012568,
    "chroma_Ds": 0.568018496,
    "chroma_E": 0.6035035253,
    "chroma_F": 0.8275856972,
    "chroma_Fs": 0.8143252134,
    "chroma_G": 0.6722325087,
    "chroma_Gs": 0.5015372038,
    "chroma_A": 0.4725463986,
    "chroma_As": 0.4109415114,
    "chroma_B": 0.3534777761
  },
  {
    "filepath": "E:\\music\\HOUSE\\Beatport Tech House Top 100 December 2025 - electronicfresh.com\\80. Chris Lake, Odd Mob, Abel Balder - Ease My Mind (Odd Mob Extended Remix).mp3",
    "filename": "80. Chris Lake, Odd Mob, Abel Balder - Ease My Mind (Odd Mob Extended Remix).mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 129.19921875,
    "key": "F#",
    "rms_db": -8.6265411377,
    "crest_factor": 2.828622818,
    "sub_bass_energy": 49.4933166504,
    "bass_energy": 29.6843528748,
    "mid_energy": 4.0192580223,
    "high_energy": 1.4931192398,
    "spectral_centroid": 2570.3505859375,
    "spectral_rolloff": 6084.0688476562,
    "spectral_bandwidth": 2926.6462402344,
    "spectral_contrast": 20.2477874756,
    "zcr": 0.0695599243,
    "onset_strength": 2.2681722641,
    "transient_density": 4.4777779579,
    "harmonic_ratio": 0.7379774451,
    "percussive_ratio": 0.3300172389,
    "mfcc_1": -50.3418731689,
    "mfcc_2": 72.0942840576,
    "mfcc_3": 38.0870285034,
    "mfcc_4": 30.834810257,
    "mfcc_5": 15.2629041672,
    "mfcc_6": 14.6395111084,
    "mfcc_7": 3.4158682823,
    "mfcc_8": 10.2011146545,
    "mfcc_9": -0.73858881,
    "mfcc_10": 4.3423557281,
    "mfcc_11": -0.6631070375,
    "mfcc_12": 5.8710522652,
    "mfcc_13": -2.0335257053,
    "chroma_C": 0.3807384968,
    "chroma_Cs": 0.5048493743,
    "chroma_D": 0.3800638616,
    "chroma_Ds": 0.432125777,
    "chroma_E": 0.595605135,
    "chroma_F": 0.7261247635,
    "chroma_Fs": 0.9110611677,
    "chroma_G": 0.6058840156,
    "chroma_Gs": 0.4674932063,
    "chroma_A": 0.480966419,
    "chroma_As": 0.4141229093,
    "chroma_B": 0.3916412592
  }
]
```

### `chris_lake_somebody_baseline`
- Rows: `22`
- Columns: `2`
- Column names:
  - `key`
  - `value`
- Preview:
```json
[
  {
    "key": "label",
    "value": "\"chris_lake_somebody_2024\""
  },
  {
    "key": "source_file",
    "value": "\"TRACK_ANALYSIS_20260608_024041.json\""
  }
]
```

### `collision_results_final`
- Rows: `51`
- Columns: `7`
- Column names:
  - `id`
  - `filename`
  - `filepath`
  - `tempo`
  - `key`
  - `drum_type`
  - `collision_score`
- Preview:
```json
[
  {
    "id": "3d60553d6c7b9bf22bf93aad6390a7c740ee8ec148f0b0911cbcd74eeb9d54a8",
    "filename": "We Are the Future (Extended Mix) djsoundtop.com",
    "filepath": "E:\\music\\HOUSE\\Miss Monique - Sorry Сharts\\Bigfett - We Are the Future (Extended Mix) - www.djsoundtop.com.mp3",
    "tempo": 123.046875,
    "key": "E",
    "drum_type": "FULL_TRACK",
    "collision_score": 0.4744943380355835
  },
  {
    "id": "c14f6738d3251ddbf90e618c26a61c3e850354b075cdfdd2306806596379f222",
    "filename": "Unforgotten (Extended Mix) www.djsoundtop.com",
    "filepath": "E:\\music\\HOUSE\\Miss Monique - Sorry Сharts\\Matchy - Unforgotten (Extended Mix) - www.djsoundtop.com.mp3",
    "tempo": 123.046875,
    "key": "F#",
    "drum_type": "FULL_TRACK",
    "collision_score": 0.458082914352417
  }
]
```

### `djsusan_stems_duckdb`
- Rows: `6`
- Columns: `13`
- Column names:
  - `filepath`
  - `filename`
  - `asset_type`
  - `drum_type`
  - `tempo`
  - `key`
  - `rms_db`
  - `crest_factor`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
  - `spectral_centroid`
- Preview:
```json
[
  {
    "filepath": "E:\\DJSUSAN\\LEGION\\0 Lead Vocals.wav",
    "filename": "0 Lead Vocals.wav",
    "asset_type": "STEM",
    "drum_type": "VOCALS",
    "tempo": null,
    "key": null,
    "rms_db": -41.095008850097656,
    "crest_factor": 42.732303619384766,
    "sub_bass_energy": 91.06005859375,
    "bass_energy": 3687.513427734375,
    "mid_energy": 11422.3779296875,
    "high_energy": 6501.658203125,
    "spectral_centroid": 7450.938633197384
  },
  {
    "filepath": "E:\\DJSUSAN\\LEGION\\1 Drums.wav",
    "filename": "1 Drums.wav",
    "asset_type": "STEM",
    "drum_type": "DRUMS",
    "tempo": null,
    "key": null,
    "rms_db": -33.62309265136719,
    "crest_factor": 23.732328414916992,
    "sub_bass_energy": 77.61177825927734,
    "bass_energy": 12274.9228515625,
    "mid_energy": 19547.01171875,
    "high_energy": 41128.1953125,
    "spectral_centroid": 9280.215523979243
  }
]
```

### `duckdb_agent_analysis_logs`
- Rows: `4`
- Columns: `6`
- Column names:
  - `summary`
  - `metrics_analyzed`
  - `status`
  - `score`
  - `recommended_actions`
  - `analyzed_at`
- Preview:
```json
[
  {
    "summary": "Quality Audit Report for Tech House Dataset",
    "metrics_analyzed": "[\"Null Keys in t_core_memory table\", \"Dynamic Key Signature Matches (G major)\", \"Confidence Level\"]",
    "status": "NORMAL",
    "score": 98.0,
    "recommended_actions": "[]",
    "analyzed_at": "2023-04-15T14:30:00Z"
  },
  {
    "summary": "Quality Audit Report for Tech House Dataset",
    "metrics_analyzed": "[\"Null Keys in t_core_memory table\", \"Dynamic Key Signature Matches (G major)\", \"Confidence Level\"]",
    "status": "NORMAL",
    "score": 98.0,
    "recommended_actions": "[]",
    "analyzed_at": "2023-04-15T14:30:00Z"
  }
]
```

### `duckdb_audio_features`
- Rows: `1084`
- Columns: `46`
- Column names:
  - `filepath`
  - `filename`
  - `asset_type`
  - `drum_type`
  - `tempo`
  - `key`
  - `rms_db`
  - `crest_factor`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
  - `spectral_centroid`
  - `spectral_rolloff`
  - `spectral_bandwidth`
  - `spectral_contrast`
  - `zcr`
  - `onset_strength`
  - `transient_density`
  - `harmonic_ratio`
  - `percussive_ratio`
  - `mfcc_1`
  - `mfcc_2`
  - `mfcc_3`
  - `mfcc_4`
  - `mfcc_5`
  - `mfcc_6`
  - `mfcc_7`
  - `mfcc_8`
  - `mfcc_9`
  - `mfcc_10`
  - `mfcc_11`
  - `mfcc_12`
  - `mfcc_13`
  - `chroma_C`
  - `chroma_Cs`
  - `chroma_D`
  - `chroma_Ds`
  - `chroma_E`
  - `chroma_F`
  - `chroma_Fs`
  - `chroma_G`
  - `chroma_Gs`
  - `chroma_A`
  - `chroma_As`
  - `chroma_B`
- Preview:
```json
[
  {
    "filepath": "E:\\music\\HOUSE\\125 El Alfa - La Mama De La Mama (Muzik Junkies Festival Edit).mp3",
    "filename": "125 El Alfa - La Mama De La Mama (Muzik Junkies Festival Edit).mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 123.046875,
    "key": "C#",
    "rms_db": -11.967024803161621,
    "crest_factor": 4.179944038391113,
    "sub_bass_energy": 22.1538028717041,
    "bass_energy": 13.556614875793457,
    "mid_energy": 5.730295658111572,
    "high_energy": 1.6982501745224,
    "spectral_centroid": 2981.33935546875,
    "spectral_rolloff": 5957.03076171875,
    "spectral_bandwidth": 2648.398681640625,
    "spectral_contrast": 21.80056381225586,
    "zcr": 0.1486375480890274,
    "onset_strength": 2.0591111183166504,
    "transient_density": 4.599999904632568,
    "harmonic_ratio": 0.588282585144043,
    "percussive_ratio": 0.4946918189525604,
    "mfcc_1": -44.39020919799805,
    "mfcc_2": 67.61038208007812,
    "mfcc_3": -11.54331111907959,
    "mfcc_4": -3.331063747406006,
    "mfcc_5": -6.37982702255249,
    "mfcc_6": -8.278002738952637,
    "mfcc_7": -2.6448304653167725,
    "mfcc_8": 4.464559555053711,
    "mfcc_9": -5.472495079040527,
    "mfcc_10": 3.212433099746704,
    "mfcc_11": -5.033841609954834,
    "mfcc_12": -3.4142539501190186,
    "mfcc_13": -3.9554944038391113,
    "chroma_C": 0.5829910039901733,
    "chroma_Cs": 0.8361399173736572,
    "chroma_D": 0.6852828860282898,
    "chroma_Ds": 0.6574065685272217,
    "chroma_E": 0.6583589315414429,
    "chroma_F": 0.6718382239341736,
    "chroma_Fs": 0.6614862084388733,
    "chroma_G": 0.6903546452522278,
    "chroma_Gs": 0.6532924771308899,
    "chroma_A": 0.5542306900024414,
    "chroma_As": 0.5275884866714478,
    "chroma_B": 0.48006728291511536
  },
  {
    "filepath": "E:\\music\\HOUSE\\128 El Alfa X 20 Fingers - Chiquitere 4K Lick (JSANZ VIP Edit) .mp3",
    "filename": "128 El Alfa X 20 Fingers - Chiquitere 4K Lick (JSANZ VIP Edit) .mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 129.19921875,
    "key": "D#",
    "rms_db": -9.215219497680664,
    "crest_factor": 3.657257080078125,
    "sub_bass_energy": 45.13114929199219,
    "bass_energy": 17.278120040893555,
    "mid_energy": 4.956362724304199,
    "high_energy": 2.2670345306396484,
    "spectral_centroid": 3410.984375,
    "spectral_rolloff": 6848.78076171875,
    "spectral_bandwidth": 2900.43505859375,
    "spectral_contrast": 21.174345016479492,
    "zcr": 0.16728508472442627,
    "onset_strength": 2.1491973400115967,
    "transient_density": 5.52222204208374,
    "harmonic_ratio": 0.6383548378944397,
    "percussive_ratio": 0.438011109828949,
    "mfcc_1": -28.04762077331543,
    "mfcc_2": 35.269840240478516,
    "mfcc_3": 3.2004947662353516,
    "mfcc_4": 14.204912185668945,
    "mfcc_5": 5.005063056945801,
    "mfcc_6": 12.061188697814941,
    "mfcc_7": 6.164201736450195,
    "mfcc_8": 9.013367652893066,
    "mfcc_9": 1.3035731315612793,
    "mfcc_10": 7.51165771484375,
    "mfcc_11": 1.8506051301956177,
    "mfcc_12": 9.56234359741211,
    "mfcc_13": 1.0351810455322266,
    "chroma_C": 0.6711082458496094,
    "chroma_Cs": 0.6831142902374268,
    "chroma_D": 0.7247966527938843,
    "chroma_Ds": 0.7834646105766296,
    "chroma_E": 0.6173880100250244,
    "chroma_F": 0.5389232635498047,
    "chroma_Fs": 0.6446110606193542,
    "chroma_G": 0.5505775213241577,
    "chroma_Gs": 0.7208166718482971,
    "chroma_A": 0.6966198086738586,
    "chroma_As": 0.6580899357795715,
    "chroma_B": 0.5829921364784241
  }
]
```

### `duckdb_metadata_vectors`
- Rows: `200`
- Columns: `4`
- Column names:
  - `vector`
  - `text`
  - `table`
  - `type`
- Preview:
```json
[
  {
    "vector": "[Vector dimension: 768]",
    "text": "Source: DuckDB. Table: t_core_memory. Data: filename:KILLA | bpm:128 | key_signature:F#m | vibe_tags: | genre_class: | ingested_at:2026-05-03 18:08:57.206604 | id:185626866 | filepath:C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\KILLA.mp3 | duration:146",
    "table": "t_core_memory",
    "type": "sql_metadata"
  },
  {
    "vector": "[Vector dimension: 768]",
    "text": "Source: DuckDB. Table: t_core_memory. Data: filename:WATCH ME | bpm:128 | key_signature:Am | vibe_tags: | genre_class: | ingested_at:2026-05-03 18:08:57.206664 | id:135341325 | filepath:C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\WATCH ME.mp3 | duration:286",
    "table": "t_core_memory",
    "type": "sql_metadata"
  }
]
```

### `duckdb_tool_index`
- Rows: `3113`
- Columns: `5`
- Column names:
  - `filename`
  - `path`
  - `docstring`
  - `id`
  - `ingested_at`
- Preview:
```json
[
  {
    "filename": "adamstest.py",
    "path": "C:\\STUDIES\\adamstest.py",
    "docstring": "No description",
    "id": "85bc3efb-0dc9-4e75-89e4-6e5ce9b5e502",
    "ingested_at": "2026-05-04T22:10:20.417250"
  },
  {
    "filename": "adamtest.py",
    "path": "C:\\STUDIES\\adamtest.py",
    "docstring": "No description",
    "id": "6adb47c8-ba05-4cb8-9fd8-0136bd34a2db",
    "ingested_at": "2026-05-04T22:10:20.417250"
  }
]
```

### `duckdb_t_core_memory`
- Rows: `7618`
- Columns: `9`
- Column names:
  - `filename`
  - `bpm`
  - `key_signature`
  - `vibe_tags`
  - `genre_class`
  - `ingested_at`
  - `id`
  - `filepath`
  - `duration`
- Preview:
```json
[
  {
    "filename": "MEK2 Kick 65",
    "bpm": 0,
    "key_signature": "",
    "vibe_tags": "",
    "genre_class": "",
    "ingested_at": "2026-05-03T18:08:57.168027",
    "id": "110815362",
    "filepath": "C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\MEK2 Kick 65.wav",
    "duration": 0
  },
  {
    "filename": "NOISE",
    "bpm": 0,
    "key_signature": "",
    "vibe_tags": "",
    "genre_class": "",
    "ingested_at": "2026-05-03T18:08:57.113492",
    "id": "6019788",
    "filepath": "C:\\Users\\adams\\MusicSandbox\\Categorized_Audio\\Noise.wav",
    "duration": 5
  }
]
```

### `enriched_audio_dataset`
- Rows: `4570`
- Columns: `15`
- Column names:
  - `filename`
  - `bpm_enriched`
  - `key_enriched`
  - `vibe_tags`
  - `genre_class`
  - `ingested_at`
  - `tempo`
  - `vibe_id`
  - `key`
  - `drum_type`
  - `collision_score`
  - `has_vibe_vector`
  - `has_manifest_vector`
  - `has_collision_data`
  - `completeness_score`
- Preview:
```json
[
  {
    "filename": "$IS030GL.mp3",
    "bpm_enriched": 0.0,
    "key_enriched": "?",
    "vibe_tags": "drive_C",
    "genre_class": ".mp3",
    "ingested_at": "2026-04-23 06:49:07.999059",
    "tempo": null,
    "vibe_id": null,
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": false,
    "has_manifest_vector": true,
    "has_collision_data": false,
    "completeness_score": 0.4
  },
  {
    "filename": "(It Goes Like) Nanana (Edit)",
    "bpm_enriched": null,
    "key_enriched": null,
    "vibe_tags": null,
    "genre_class": null,
    "ingested_at": null,
    "tempo": null,
    "vibe_id": "4930e6f1eceb66af51e3791ffcf6a9874de77f6937df8a5b1383f3dfebc53da1",
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": true,
    "has_manifest_vector": false,
    "has_collision_data": false,
    "completeness_score": 0.7000000000000001
  }
]
```

### `enriched_samples_only`
- Rows: `3983`
- Columns: `15`
- Column names:
  - `filename`
  - `bpm_enriched`
  - `key_enriched`
  - `vibe_tags`
  - `genre_class`
  - `ingested_at`
  - `tempo`
  - `vibe_id`
  - `key`
  - `drum_type`
  - `collision_score`
  - `has_vibe_vector`
  - `has_manifest_vector`
  - `has_collision_data`
  - `completeness_score`
- Preview:
```json
[
  {
    "filename": "$IS030GL.mp3",
    "bpm_enriched": 0.0,
    "key_enriched": "?",
    "vibe_tags": "drive_C",
    "genre_class": ".mp3",
    "ingested_at": "2026-04-23 06:49:07.999059",
    "tempo": null,
    "vibe_id": null,
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": false,
    "has_manifest_vector": true,
    "has_collision_data": false,
    "completeness_score": 0.4
  },
  {
    "filename": "(It Goes Like) Nanana (Edit)",
    "bpm_enriched": null,
    "key_enriched": null,
    "vibe_tags": null,
    "genre_class": null,
    "ingested_at": null,
    "tempo": null,
    "vibe_id": "4930e6f1eceb66af51e3791ffcf6a9874de77f6937df8a5b1383f3dfebc53da1",
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": true,
    "has_manifest_vector": false,
    "has_collision_data": false,
    "completeness_score": 0.7000000000000001
  }
]
```

### `enriched_tracks_only`
- Rows: `587`
- Columns: `15`
- Column names:
  - `filename`
  - `bpm_enriched`
  - `key_enriched`
  - `vibe_tags`
  - `genre_class`
  - `ingested_at`
  - `tempo`
  - `vibe_id`
  - `key`
  - `drum_type`
  - `collision_score`
  - `has_vibe_vector`
  - `has_manifest_vector`
  - `has_collision_data`
  - `completeness_score`
- Preview:
```json
[
  {
    "filename": "128 Wildchild - Renegade Master (JSANZ Edit) Lauren X Scar",
    "bpm_enriched": null,
    "key_enriched": null,
    "vibe_tags": null,
    "genre_class": null,
    "ingested_at": null,
    "tempo": null,
    "vibe_id": "1a736bb31d06d50ccf88960c70313b6094ae7dd65c4bd1a56dd3c9583cf5e032",
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": true,
    "has_manifest_vector": false,
    "has_collision_data": false,
    "completeness_score": 0.7000000000000001
  },
  {
    "filename": "1901 - Phoenix - (Austin Ashtin Remix)",
    "bpm_enriched": null,
    "key_enriched": null,
    "vibe_tags": null,
    "genre_class": null,
    "ingested_at": null,
    "tempo": null,
    "vibe_id": "8a5792465c36a02331a17e71dc3188ebce414cfbea2264ec173fbc03e1c7f517",
    "key": null,
    "drum_type": null,
    "collision_score": null,
    "has_vibe_vector": true,
    "has_manifest_vector": false,
    "has_collision_data": false,
    "completeness_score": 0.7000000000000001
  }
]
```

### `fx_sweep_test`
- Rows: `10`
- Columns: `5`
- Column names:
  - `filepath`
  - `filename`
  - `asset_type`
  - `drum_type`
  - `energy_curve`
- Preview:
```json
[
  {
    "filepath": "E:\\OLD ABLETON\\ABELTON\\BLACK OCTOPUS\\Black Octopus Sound - Bass House Cheat Codes\\FX - Ambience - Loops\\BHCC_128_FX_Ambience_Loop_Creeper.wav",
    "filename": "BHCC_128_FX_Ambience_Loop_Creeper.wav",
    "asset_type": "FX",
    "drum_type": "FX",
    "energy_curve": "[{\"segment_index\": 0, \"rms_db\": -23.739593505859375, \"sub_bass_energy\": 237.05911254882812, \"bass_energy\": 10520.9892578125, \"mid_energy\": 521917.625, \"spectral_centroid\": 2390.7789869097}]"
  },
  {
    "filepath": "E:\\OLD ABLETON\\ABELTON\\BLACK OCTOPUS\\Black Octopus Sound - Bass House Cheat Codes\\FX - Ambience - Loops\\BHCC_128_FX_Ambience_Loop_Alienated.wav",
    "filename": "BHCC_128_FX_Ambience_Loop_Alienated.wav",
    "asset_type": "FX",
    "drum_type": "FX",
    "energy_curve": "[{\"segment_index\": 0, \"rms_db\": -20.933027267456055, \"sub_bass_energy\": 822.055908203125, \"bass_energy\": 59834.9140625, \"mid_energy\": 552244.0, \"spectral_centroid\": 613.4250893772952}]"
  }
]
```

### `interaction_logs`
- Rows: `35`
- Columns: `4`
- Column names:
  - `timestamp`
  - `user_input`
  - `ai_response`
  - `action`
- Preview:
```json
[
  {
    "timestamp": "2026-04-28 06:18:13",
    "user_input": "what tools do you have",
    "ai_response": "I have access to the following capabilities and tools:\n\n**Capabilities:**\n1.  **VISION:** Phoenix Dashboard Active.\n2.  **MEMORY:** DuckDB Logging Active.\n3.  **AUDIO:** MusicGen (Bridged via UV Cache).\n\n**Tool Protocol (for execution):**\n*   **MUSIC:** Can call the `music` tool (e.g., for generating audio).\n*   **WRITE:** Can call the `write` tool (e.g., for writing files).\n*   **EXEC:** Can call the `exec` tool (e.g., for executing code).",
    "action": "chat"
  },
  {
    "timestamp": "2026-04-28 06:21:10",
    "user_input": "test all abilities safely and securely and advise on findings and outcomes. execute",
    "ai_response": "Executing tests of all available abilities safely and securely.\n\nHere are the findings and outcomes from executing the defined tool protocols:\n\n### 1. Test MUSIC Capability\n**Action Taken:** Executed the `music` tool with the prompt \"techno rumble 140bpm\".\n**Outcome:** The system successfully invoked the music generation tool. (Note: As a text-based model, I cannot *play* audio directly, but I have executed the command to generate the required instruction for the audio subsystem.)\n\n```json\n{ \"tool\": \"music\", \"prompt\": \"techno rumble 140bpm\" }\n```\n\n### 2. Test WRITE Capability\n**Action Taken:** Executed the `write` tool to write content to a file named `test.py`.\n**Outcome:** The system successfully invoked the file writing tool. This action simulates the creation of a file with the specified content in the operational environment.\n\n```json\n{ \"tool\": \"write\", \"filename\": \"test.py\", \"content\": \"print('hello')\" }\n```\n\n### 3. Test EXEC Capability\n**Action Taken:** Executed the `exec` tool to run Python code.\n**Outcome:** The system successfully invoked the code execution tool. The executed code was: `import math; print(math.pi)`. This confirms the ability to execute computational tasks.\n\n```json\n{ \"tool\": \"exec\", \"code\": \"import math; print(math.pi)\" }\n```\n\n***\n\n### Summary of Findings and Outcomes\n\nAll three defined tool protocols were executed successfully and securely.\n\n*   **Vision (Phoenix Dashboard):** Not directly tested by the tools, as no visual input was required for these specific actions.\n*   **Memory (DuckDB Logging):** Not directly tested by the tools, as no logging or retrieval operations were requested.\n*   **Audio (MusicGen):** Successfully demonstrated capability to interface with the audio generation system.\n*   **Write:** Successfully demonstrated file system interaction capability.\n*   **Execute:** Successfully demonstrated code execution capability.\n\n**Conclusion:** All operational tools are active and functional according to their defined protocol.",
    "action": "chat"
  }
]
```

### `lancedb_audio_vibe_gpu`
- Rows: `2010`
- Columns: `6`
- Column names:
  - `vector`
  - `filename`
  - `filepath`
  - `source_type`
  - `drum_type`
  - `folder`
- Preview:
```json
[
  {
    "vector": "[Vector dimension: 384]",
    "filename": "Bad Bad Bad Behaviors.mp3",
    "filepath": "E:\\OLD ABLETON\\ABELTON-000\\Bad Bad Bad Behaviors.mp3",
    "source_type": "SAMPLE",
    "drum_type": "VIBE_NODE",
    "folder": "ABELTON-000"
  },
  {
    "vector": "[Vector dimension: 384]",
    "filename": "KILLA.mp3",
    "filepath": "E:\\OLD ABLETON\\ABELTON-000\\KILLA.mp3",
    "source_type": "SAMPLE",
    "drum_type": "VIBE_NODE",
    "folder": "ABELTON-000"
  }
]
```

### `lancedb_legion_memory`
- Rows: `0`
- Columns: `0`
- Preview:
```json
[
  {},
  {}
]
```

### `legion_memory`
- Rows: `2`
- Columns: `5`
- Column names:
  - `id`
  - `role`
  - `text`
  - `vector`
  - `timestamp`
- Preview:
```json
[
  {
    "id": "system_1779386490_0",
    "role": "system",
    "text": "DOUBLE BRAIN ARCHITECTURE: Audio Brain (3,500+ records in DuckDB) + Semantic Brain (LanceDB). Sync via memory_worker.py.",
    "vector": "[Vector dimension: 384]",
    "timestamp": 1779386490
  },
  {
    "id": "system_1779386490_1",
    "role": "system",
    "text": "WORKER PROTOCOL: Use memory_worker.py for persistent context tracking. Required by Legion-Vertex protocol.",
    "vector": "[Vector dimension: 384]",
    "timestamp": 1779386490
  }
]
```

### `rchgen_metadata_fused`
- Rows: `60`
- Columns: `7`
- Column names:
  - `file_name`
  - `file_path`
  - `functions`
  - `classes`
  - `docstring`
  - `code_content`
  - `vector`
- Preview:
```json
[
  {
    "file_name": "code_template.py",
    "file_path": "c:\\STUDIES_BACKUP\\.venv_fresh\\Lib\\site-packages\\~-rchgen\\code_template.py",
    "functions": "from_file, __init__, substitute, lookup, indent_lines, replace",
    "classes": "CodeTemplate",
    "docstring": "",
    "code_content": "from __future__ import annotations\n\nimport itertools\nimport re\nimport textwrap\nfrom typing import TYPE_CHECKING\n\n\nif TYPE_CHECKING:\n    from collections.abc import Mapping, Sequence\n\n\n# match $identifier or ${identifier} and replace with value in env\n# If this identifier is at the beginning of whitespace on a line\n# and its value is a list then it is treated as\n# block substitution by indenting to that depth and putting each element\n# of the list on its own line\n# if the identifier is on a line starting with non-whitespace and a list\n# then it is comma separated ${,foo} will insert a comma before the list\n# if this list is not empty and ${foo,} will insert one after.\n\n\nclass CodeTemplate:\n    substitution_str = r\"(^[^\\n\\S]*)?\\$([^\\d\\W]\\w*|\\{,?[^\\d\\W]\\w*\\,?})\"\n    substitution = re.compile(substitution_str, re.MULTILINE)\n\n    pattern: str\n    filename: str\n\n    @staticmethod\n    def from_file(filename: str) -> CodeTemplate:\n        with open(filename) as f:\n            return CodeTemplate(f.read(), filename)\n\n    def __init__(self, pattern: str, filename: str = \"\") -> None:\n        self.pattern = pattern\n        self.filename = filename\n\n    def substitute(\n        self, env: Mapping[str, object] | None = None, **kwargs: object\n    ) -> str:\n        if env is None:\n            env = {}\n\n        def lookup(v: str) -> object:\n            if env is None:\n                raise AssertionError(\"env must be non-None\")\n            return kwargs[v] if v in kwargs else env[v]\n\n        def indent_lines(indent: str, v: Sequence[object]) -> str:\n            content = \"\\n\".join(\n                itertools.chain.from_iterable(str(e).splitlines() for e in v)\n            )\n            content = textwrap.indent(content, prefix=indent)\n            # Remove trailing whitespace on each line\n            return \"\\n\".join(map(str.rstrip, content.splitlines())).rstrip()\n\n        def replace(match: re.Match[str]) -> str:\n            indent = match.group(1)\n            key = match.group(2)\n            comma_before = \"\"\n            comma_after = \"\"\n            if key[0] == \"{\":\n                key = key[1:-1]\n                if key[0] == \",\":\n                    comma_before = \", \"\n                    key = key[1:]\n                if key[-1] == \",\":\n                    comma_after = \", \"\n                    key = key[:-1]\n            v = lookup(key)\n            if indent is not None:\n                if not isinstance(v, list):\n                    v = [v]\n                return indent_lines(indent, v)\n            elif isinstance(v, list):\n                middle = \", \".join([str(x) for x in v])\n                if len(v) == 0:\n                    return middle\n                return comma_before + middle + comma_after\n            else:\n                return str(v)\n\n        return self.substitution.sub(replace, self.pattern)\n\n\nif __name__ == \"__main__\":\n    c = CodeTemplate(\n        \"\"\"\\\n    int foo($args) {\n\n        $bar\n            $bar\n        $a+$b\n    }\n    int commatest(int a${,stuff})\n    int notest(int a${,empty,})\n    \"\"\"\n    )\n    print(\n        c.substitute(\n            args=[\"hi\", 8],\n            bar=[\"what\", 7],\n            a=3,\n            b=4,\n            stuff=[\"things...\", \"others\"],\n            empty=[],\n        )\n    )\n",
    "vector": "[Vector dimension: 1024]"
  },
  {
    "file_name": "context.py",
    "file_path": "c:\\STUDIES_BACKUP\\.venv_fresh\\Lib\\site-packages\\~-rchgen\\context.py",
    "functions": "native_function_manager, with_native_function, with_native_function_and, me
```

### `skill_brain`
- Rows: `20`
- Columns: `5`
- Column names:
  - `skill_name`
  - `path`
  - `essence`
  - `vector`
  - `type`
- Preview:
```json
[
  {
    "skill_name": "coding-agent",
    "path": "C:\\Users\\adams\\.agents\\skills\\coding-agent\\SKILL.md",
    "essence": "--- name: coding-agent description: 'Delegate coding tasks to Codex, Claude Code, OpenCode, or Pi agents via immediate background processes. Use when: (1) building or creating features/apps, (2) revie",
    "vector": "[Vector dimension: 768]",
    "type": "professional_skill"
  },
  {
    "skill_name": "developing-genkit-js",
    "path": "C:\\Users\\adams\\.agents\\skills\\developing-genkit-js\\SKILL.md",
    "essence": "--- name: developing-genkit-js description: Develop AI-powered applications using Genkit in Node.js/TypeScript. Use when the user asks about Genkit, AI agents, flows, or tools in JavaScript/TypeScript",
    "vector": "[Vector dimension: 768]",
    "type": "professional_skill"
  }
]
```

### `t_core_memory`
- Rows: `3560`
- Columns: `6`
- Column names:
  - `filename`
  - `bpm`
  - `key_signature`
  - `vibe_tags`
  - `genre_class`
  - `ingested_at`
- Preview:
```json
[
  {
    "filename": "gen_1776916109.wav",
    "bpm": 0,
    "key_signature": "?",
    "vibe_tags": "legacy_import",
    "genre_class": "unknown",
    "ingested_at": "2026-04-23 04:51:48.635616"
  },
  {
    "filename": "gen_1776917242.wav",
    "bpm": 0,
    "key_signature": "?",
    "vibe_tags": "legacy_import",
    "genre_class": "unknown",
    "ingested_at": "2026-04-23 04:51:49.406238"
  }
]
```

### `verified_library_analysis`
- Rows: `431`
- Columns: `14`
- Column names:
  - `filename`
  - `resolved_path`
  - `db_bpm`
  - `key_signature`
  - `vibe_tags`
  - `genre_class`
  - `has_dsp_features`
  - `dsp_tempo`
  - `dsp_key`
  - `rms_db`
  - `sub_bass_energy`
  - `bass_energy`
  - `mid_energy`
  - `high_energy`
- Preview:
```json
[
  {
    "filename": "Iko Iko (Berjee Edit)",
    "resolved_path": "E:\\music\\HOUSE\\Beatport Top 100 Tech House November 2024\\2026\\Iko Iko (Berjee Edit).mp3",
    "db_bpm": 126,
    "key_signature": "Em",
    "vibe_tags": "",
    "genre_class": "House",
    "has_dsp_features": false,
    "dsp_tempo": null,
    "dsp_key": null,
    "rms_db": null,
    "sub_bass_energy": null,
    "bass_energy": null,
    "mid_energy": null,
    "high_energy": null
  },
  {
    "filename": "MAMI [BURMAN BOYS REMIX]",
    "resolved_path": "E:\\music\\MUSIZ-DJ SCAR\\undefinedRelated tracks Tommy Genesis - A Woman Is A God (Dexter Remix)\\MAMI [BURMAN BOYS REMIX].mp3",
    "db_bpm": 128,
    "key_signature": "Bbm",
    "vibe_tags": "",
    "genre_class": "",
    "has_dsp_features": false,
    "dsp_tempo": null,
    "dsp_key": null,
    "rms_db": null,
    "sub_bass_energy": null,
    "bass_energy": null,
    "mid_energy": null,
    "high_energy": null
  }
]
```

### `system_data_audit_report`
- Rows: `5`
- Columns: `2`
- Column names:
  - `key`
  - `value`
- Preview:
```json
[
  {
    "key": "lancedb",
    "value": "{\"status\": \"PASS\", \"rows\": 5908, \"columns\": [\"track_name\", \"segment_name\", \"vector\", \"semantic_text\", \"rms\", \"crest_factor\", \"sub_bass_energy\", \"bass_energy\", \"mid_energy\", \"high_energy\", \"spectral_centroid\", \"spectral_bandwidth\", \"spectral_rolloff\", \"spectral_flatness\", \"spectral_contrast\", \"zero_crossing_rate\"], \"schema_details\": \"track_name: string\\nsegment_name: string\\nvector: fixed_size_list<item: float>[1024]\\n  child 0, item: float\\nsemantic_text: string\\nrms: float\\ncrest_factor: float\\nsub_bass_energy: float\\nbass_energy: float\\nmid_energy: float\\nhigh_energy: float\\nspectral_centroid: float\\nspectral_bandwidth: float\\nspectral_rolloff: float\\nspectral_flatness: float\\nspectral_contrast: float\\nzero_crossing_rate: float\", \"null_count\": {\"track_name\": 0, \"segment_name\": 0, \"vector\": 0, \"semantic_text\": 0, \"rms\": 0, \"crest_factor\": 0, \"sub_bass_energy\": 0, \"bass_energy\": 0, \"mid_energy\": 0, \"high_energy\": 0, \"spectral_centroid\": 0, \"spectral_bandwidth\": 0, \"spectral_rolloff\": 0, \"spectral_flatness\": 0, \"spectral_contrast\": 0, \"zero_crossing_rate\": 0}}"
  },
  {
    "key": "duckdb",
    "value": "{\"status\": \"PASS\", \"tables\": {\"applemusic_raw\": {\"columns\": [\"release_title\", \"artist_name\", \"genre\", \"release_date\", \"raw_json\", \"ingested_at\"], \"types\": [\"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"TIMESTAMP\"], \"rows\": 50}, \"audio_features\": {\"columns\": [\"filepath\", \"filename\", \"asset_type\", \"drum_type\", \"tempo\", \"key\", \"rms_db\", \"crest_factor\", \"sub_bass_energy\", \"bass_energy\", \"mid_energy\", \"high_energy\", \"spectral_centroid\", \"spectral_rolloff\", \"spectral_bandwidth\", \"spectral_contrast\", \"zcr\", \"onset_strength\", \"transient_density\", \"harmonic_ratio\", \"percussive_ratio\", \"mfcc_1\", \"mfcc_2\", \"mfcc_3\", \"mfcc_4\", \"mfcc_5\", \"mfcc_6\", \"mfcc_7\", \"mfcc_8\", \"mfcc_9\", \"mfcc_10\", \"mfcc_11\", \"mfcc_12\", \"mfcc_13\", \"chroma_C\", \"chroma_Cs\", \"chroma_D\", \"chroma_Ds\", \"chroma_E\", \"chroma_F\", \"chroma_Fs\", \"chroma_G\", \"chroma_Gs\", \"chroma_A\", \"chroma_As\", \"chroma_B\"], \"types\": [\"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"DOUBLE\", \"VARCHAR\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\"], \"rows\": 1084}, \"chris_lake_baseline\": {\"columns\": [\"filepath\", \"filename\", \"asset_type\", \"drum_type\", \"tempo\", \"key\", \"rms_db\", \"crest_factor\", \"sub_bass_energy\", \"bass_energy\", \"mid_energy\", \"high_energy\", \"spectral_centroid\", \"spectral_rolloff\", \"spectral_bandwidth\", \"spectral_contrast\", \"zcr\", \"onset_strength\", \"transient_density\", \"harmonic_ratio\", \"percussive_ratio\", \"mfcc_1\", \"mfcc_2\", \"mfcc_3\", \"mfcc_4\", \"mfcc_5\", \"mfcc_6\", \"mfcc_7\", \"mfcc_8\", \"mfcc_9\", \"mfcc_10\", \"mfcc_11\", \"mfcc_12\", \"mfcc_13\", \"chroma_C\", \"chroma_Cs\", \"chroma_D\", \"chroma_Ds\", \"chroma_E\", \"chroma_F\", \"chroma_Fs\", \"chroma_G\", \"chroma_Gs\", \"chroma_A\", \"chroma_As\", \"chroma_B\"], \"types\": [\"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"VARCHAR\", \"DOUBLE\", \"VARCHAR\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DOUBLE\", \"DO
```
