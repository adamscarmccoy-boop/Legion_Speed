# Ray Registry Table: `duckdb_audio_features`

- Created: `2026-07-03T00:19:16.507429`
- Registry: `SwarmKnowledgeRegistry`
- Type: `Table`
- Rows: `1084`
- Columns: `46`

## Columns
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

## Schema
- `pyarrow.Field<filepath: string>`
- `pyarrow.Field<filename: string>`
- `pyarrow.Field<asset_type: string>`
- `pyarrow.Field<drum_type: string>`
- `pyarrow.Field<tempo: double>`
- `pyarrow.Field<key: string>`
- `pyarrow.Field<rms_db: double>`
- `pyarrow.Field<crest_factor: double>`
- `pyarrow.Field<sub_bass_energy: double>`
- `pyarrow.Field<bass_energy: double>`
- `pyarrow.Field<mid_energy: double>`
- `pyarrow.Field<high_energy: double>`
- `pyarrow.Field<spectral_centroid: double>`
- `pyarrow.Field<spectral_rolloff: double>`
- `pyarrow.Field<spectral_bandwidth: double>`
- `pyarrow.Field<spectral_contrast: double>`
- `pyarrow.Field<zcr: double>`
- `pyarrow.Field<onset_strength: double>`
- `pyarrow.Field<transient_density: double>`
- `pyarrow.Field<harmonic_ratio: double>`
- `pyarrow.Field<percussive_ratio: double>`
- `pyarrow.Field<mfcc_1: double>`
- `pyarrow.Field<mfcc_2: double>`
- `pyarrow.Field<mfcc_3: double>`
- `pyarrow.Field<mfcc_4: double>`
- `pyarrow.Field<mfcc_5: double>`
- `pyarrow.Field<mfcc_6: double>`
- `pyarrow.Field<mfcc_7: double>`
- `pyarrow.Field<mfcc_8: double>`
- `pyarrow.Field<mfcc_9: double>`
- `pyarrow.Field<mfcc_10: double>`
- `pyarrow.Field<mfcc_11: double>`
- `pyarrow.Field<mfcc_12: double>`
- `pyarrow.Field<mfcc_13: double>`
- `pyarrow.Field<chroma_C: double>`
- `pyarrow.Field<chroma_Cs: double>`
- `pyarrow.Field<chroma_D: double>`
- `pyarrow.Field<chroma_Ds: double>`
- `pyarrow.Field<chroma_E: double>`
- `pyarrow.Field<chroma_F: double>`
- `pyarrow.Field<chroma_Fs: double>`
- `pyarrow.Field<chroma_G: double>`
- `pyarrow.Field<chroma_Gs: double>`
- `pyarrow.Field<chroma_A: double>`
- `pyarrow.Field<chroma_As: double>`
- `pyarrow.Field<chroma_B: double>`

## Preview
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
  },
  {
    "filepath": "E:\\music\\HOUSE\\125 HUGEL & Nfasis - Como Shakira (Extended Mix).mp3",
    "filename": "125 HUGEL & Nfasis - Como Shakira (Extended Mix).mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 123.046875,
    "key": "G",
    "rms_db": -12.248177528381348,
    "crest_factor": 4.456172943115234,
    "sub_bass_energy": 29.70991325378418,
    "bass_energy": 13.802984237670898,
    "mid_energy": 4.574909210205078,
    "high_energy": 1.3427907228469849,
    "spectral_centroid": 2952.679443359375,
    "spectral_rolloff": 6444.552734375,
    "spectral_bandwidth": 2886.580810546875,
    "spectral_contrast": 18.84025764465332,
    "zcr": 0.12991531193256378,
    "onset_strength": 2.464945077896118,
    "transient_density": 6.611111164093018,
    "harmonic_ratio": 0.5675854682922363,
    "percussive_ratio": 0.4911448061466217,
    "mfcc_1": -46.88602066040039,
    "mfcc_2": 63.71746826171875,
    "mfcc_3": 3.010334014892578,
    "mfcc_4": 11.819758415222168,
    "mfcc_5": 3.7732315063476562,
    "mfcc_6": 8.253338813781738,
    "mfcc_7": 0.09525036811828613,
    "mfcc_8": 3.7906653881073,
    "mfcc_9": -1.209252119064331,
    "mfcc_10": 5.003508567810059,
    "mfcc_11": -0.9669363498687744,
    "mfcc_12": 4.373715400695801,
    "mfcc_13": -1.0718262195587158,
    "chroma_C": 0.6719490885734558,
    "chroma_Cs": 0.5266191959381104,
    "chroma_D": 0.4949459135532379,
    "chroma_Ds": 0.4836070239543915,
    "chroma_E": 0.5655387043952942,
    "chroma_F": 0.6793254613876343,
    "chroma_Fs": 0.805923342704773,
    "chroma_G": 0.8521811366081238,
    "chroma_Gs": 0.5662813186645508,
    "chroma_A": 0.573799729347229,
    "chroma_As": 0.5991668701171875,
    "chroma_B": 0.5704147219657898
  },
  {
    "filepath": "E:\\music\\HOUSE\\126 David Guetta ft. Sia - Titanium (SUNGYOO Remix).mp3",
    "filename": "126 David Guetta ft. Sia - Titanium (SUNGYOO Remix).mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 123.046875,
    "key": "C",
    "rms_db": -10.533973693847656,
    "crest_factor": 4.654473781585693,
    "sub_bass_energy": 28.073776245117188,
    "bass_energy": 21.33610725402832,
    "mid_energy": 5.604825019836426,
    "high_energy": 2.2132279872894287,
    "spectral_centroid": 3369.39501953125,
    "spectral_rolloff": 7384.48876953125,
    "spectral_bandwidth": 3116.2529296875,
    "spectral_contrast": 21.642433166503906,
    "zcr": 0.15951453149318695,
    "onset_strength": 1.989601969718933,
    "transient_density": 4.633333206176758,
    "harmonic_ratio": 0.689137876033783,
    "percussive_ratio": 0.4075608551502228,
    "mfcc_1": -12.815099716186523,
    "mfcc_2": 58.74794387817383,
    "mfcc_3": 19.134517669677734,
    "mfcc_4": 14.980786323547363,
    "mfcc_5": 5.392595291137695,
    "mfcc_6": 5.111451148986816,
    "mfcc_7": 10.438516616821289,
    "mfcc_8": -1.2871780395507812,
    "mfcc_9": 2.5417897701263428,
    "mfcc_10": 4.424676895141602,
    "mfcc_11": -2.010005235671997,
    "mfcc_12": 1.1552090644836426,
    "mfcc_13": -4.036214351654053,
    "chroma_C": 0.7266150116920471,
    "chroma_Cs": 0.4961754381656647,
    "chroma_D": 0.5296455025672913,
    "chroma_Ds": 0.5219760537147522,
    "chroma_E": 0.4540914297103882,
    "chroma_F": 0.47474929690361023,
    "chroma_Fs": 0.5001540184020996,
    "chroma_G": 0.6907287240028381,
    "chroma_Gs": 0.6434935331344604,
    "chroma_A": 0.5406762361526489,
    "chroma_As": 0.6087294220924377,
    "chroma_B": 0.5762148499488831
  },
  {
    "filepath": "E:\\music\\HOUSE\\128 Daft Punk - One More Time (JSANZ Edit) Medun Rmx.mp3",
    "filename": "128 Daft Punk - One More Time (JSANZ Edit) Medun Rmx.mp3",
    "asset_type": "SONG",
    "drum_type": "FULL_TRACK",
    "tempo": 129.19921875,
    "key": "G",
    "rms_db": -10.469622611999512,
    "crest_factor": 4.511444091796875,
    "sub_bass_energy": 25.182260513305664,
    "bass_energy": 20.89472007751465,
    "mid_energy": 5.325509071350098,
    "high_energy": 2.57631778717041,
    "spectral_centroid": 3537.745361328125,
    "spectral_rolloff": 7150.04833984375,
    "spectral_bandwidth": 2966.52880859375,
    "spectral_contrast": 22.466781616210938,
    "zcr": 0.17428945004940033,
    "onset_strength": 1.3817983865737915,
    "transient_density": 1.3333333730697632,
    "harmonic_ratio": 0.7135756015777588,
    "percussive_ratio": 0.39698508381843567,
    "mfcc_1": 7.10986852645874,
    "mfcc_2": 44.40245819091797,
    "mfcc_3": 5.497219562530518,
    "mfcc_4": 21.096969604492188,
    "mfcc_5": 8.81688404083252,
    "mfcc_6": 13.989603042602539,
    "mfcc_7": 1.6260491609573364,
    "mfcc_8": 7.289217472076416,
    "mfcc_9": -3.7938835620880127,
    "mfcc_10": 2.692078113555908,
    "mfcc_11": -3.496549367904663,
    "mfcc_12": 1.6320635080337524,
    "mfcc_13": -1.4708434343338013,
    "chroma_C": 0.3888201415538788,
    "chroma_Cs": 0.4635310173034668,
    "chroma_D": 0.5822120904922485,
    "chroma_Ds": 0.38516876101493835,
    "chroma_E": 0.4866570234298706,
    "chroma_F": 0.5308728218078613,
    "chroma_Fs": 0.6715595126152039,
    "chroma_G": 0.7371991276741028,
    "chroma_Gs": 0.4836118519306183,
    "chroma_A": 0.5711551904678345,
    "chroma_As": 0.4406909942626953,
    "chroma_B": 0.479476660490036
  }
]
```