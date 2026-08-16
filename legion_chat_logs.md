26-08-11 02:42:00  [INFO]
 [nvidia/nemotron-3-nano-4b] Running chat completion on conversation with 2 messages.
2026-08-11 02:42:00  [INFO]
 [nvidia/nemotron-3-nano-4b] Streaming response...
2026-08-11 02:42:00 [DEBUG]
 7253.11.670.455 I srv  server_strea: conv_id= (empty=1)
2026-08-11 02:42:00 [DEBUG]
 7253.11.714.343 I srv    operator(): chat format: peg-native
2026-08-11 02:42:00 [DEBUG]
 7253.11.714.607 I slot get_availabl: id  0 | task -1 | selected slot by LCP similarity, sim_best = 0.260 (> 0.100 thold), f_keep = 0.215
7253.11.714.610 I srv  get_availabl: updating prompt cache
7253.11.714.689 I srv   prompt_save:  - saving prompt with length 512, total state size = 83.344 MiB (draft: 0.000 MiB)
2026-08-11 02:42:00 [DEBUG]
 7253.11.781.733 I srv          load:  - looking for better prompt, base f_keep = 0.215, sim = 0.260
2026-08-11 02:42:00 [DEBUG]
 7253.11.781.748 I srv        update:  - cache state: 20 prompts, 8045.556 MiB (limits: 8192.000 MiB, 31488 tokens, 154027 est)
7253.11.781.759 I srv        update:    - prompt 0000029C1988C080:     500 tokens, checkpoints:  2,   245.468 MiB
7253.11.781.761 I srv        update:    - prompt 0000029C1988C1A0:    1014 tokens, checkpoints:  4,   409.910 MiB
7253.11.781.762 I srv        update:    - prompt 0000029C6CE5CA50:    4936 tokens, checkpoints:  4,   427.190 MiB
7253.11.781.763 I srv        update:    - prompt 0000029C19670FC0:    4548 tokens, checkpoints:  4,   425.480 MiB
7253.11.781.809 I srv        update:    - prompt 0000029C19670E10:   15578 tokens, checkpoints:  4,   474.078 MiB
7253.11.781.814 I srv        update:    - prompt 0000029C6BBB35A0:   31025 tokens, checkpoints:  6,   704.314 MiB
7253.11.781.815 I srv        update:    - prompt 0000029C6CE5C300:   14321 tokens, checkpoints:  4,   468.540 MiB
7253.11.781.816 I srv        update:    - prompt 0000029C6CE5CDB0:     455 tokens, checkpoints:  2,   245.270 MiB
7253.11.781.818 I srv        update:    - prompt 0000029C6CE5CE40:    2070 tokens, checkpoints:  4,   414.562 MiB
7253.11.781.821 I srv        update:    - prompt 0000029C1988C3E0:   10319 tokens, checkpoints:  5,   531.996 MiB
7253.11.781.823 I srv        update:    - prompt 0000029C6CE5C540:    7160 tokens, checkpoints:  4,   436.989 MiB
7253.11.781.824 I srv        update:    - prompt 0000029C6CE5BFA0:    5343 tokens, checkpoints:  4,   428.983 MiB
7253.11.781.825 I srv        update:    - prompt 0000029C19671560:   21017 tokens, checkpoints:  5,   579.131 MiB
7253.11.781.826 I srv        update:    - prompt 0000029C19670CF0:    5391 tokens, checkpoints:  3,   348.106 MiB
7253.11.781.827 I srv        update:    - prompt 0000029C283A0600:    3650 tokens, checkpoints:  4,   421.524 MiB
7253.11.781.829 I srv        update:    - prompt 0000029C283A0CC0:    5420 tokens, checkpoints:  3,   348.234 MiB
7253.11.781.831 I srv        update:    - prompt 0000029C283A0840:    6774 tokens, checkpoints:  2,   273.111 MiB
7253.11.781.832 I srv        update:    - prompt 0000029C283A0D50:   11049 tokens, checkpoints:  3,   373.035 MiB
7253.11.781.833 I srv        update:    - prompt 0000029C283A02A0:     192 tokens, checkpoints:  2,   244.111 MiB
7253.11.781.834 I srv        update:    - prompt 0000029C283A0210:     512 tokens, checkpoints:  2,   245.521 MiB
7253.11.781.836 I srv  get_availabl: prompt cache update took 67.23 ms
7253.11.782.018 I slot launch_slot_: id  0 | task -1 | sampler chain: logits -> penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
7253.11.782.032 I slot launch_slot_: id  0 | task -1 | sampler params:
 repeat_last_n = 64, repeat_penalty = 1.100, frequency_penalty = 0.000, presence_penalty = 0.000
 dry_multiplier = 0.000, dry_base = 1.750, dry_allowed_length = 2, dry_penalty_last_n = 31488
 top_k = 40, top_p = 0.950, min_p = 0.050, xtc_probability = 0.000, xtc_threshold = 0.100, typical_p = 1.000, top_n_sigma = -1.000, temp = 0.300
 mirostat = 0, mirostat_lr = 0.100, mirostat_ent = 5.000, adaptive_target = -1.000, adaptive_decay = 0.900
7253.11.782.035 I slot launch_slot_: id  0 | task 44464 | processing task, is_child = 0
7253.11.782.036 I slot process_sing: id  1 | task -1 | saving idle slot to prompt cache
7253.11.782.037 I slot prompt_clear: id  1 | task -1 | clearing prompt with 0 tokens
7253.11.782.072 I slot process_sing: id  2 | task -1 | saving idle slot to prompt cache
7253.11.782.075 I slot prompt_clear: id  2 | task -1 | clearing prompt with 0 tokens
7253.11.782.101 I slot process_sing: id  3 | task -1 | saving idle slot to prompt cache
7253.11.782.104 I slot prompt_clear: id  3 | task -1 | clearing prompt with 0 tokens
7253.11.782.139 I slot   operator(): id  0 | task 44464 | new prompt, n_ctx_slot = 31488, n_keep = 0, task.n_tokens = 423
7253.11.782.144 I slot   operator(): id  0 | task 44464 | checking checkpoint with [170, 170] against 110...
7253.11.782.145 I slot   operator(): id  0 | task 44464 | checking checkpoint with [146, 146] against 110...
7253.11.782.147 I slot   operator(): id  0 | task 44464 | forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory, see <https://github.com/ggml-org/llama.cpp/pull/13194#issuecomment-2868343055>)
7253.11.782.149 I slot   operator(): id  0 | task 44464 | erased invalidated context checkpoint (pos_min = 146, pos_max = 146, n_tokens = 147, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:00 [DEBUG]
 7253.11.785.675 I slot   operator(): id  0 | task 44464 | erased invalidated context checkpoint (pos_min = 170, pos_max = 170, n_tokens = 171, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:00 [DEBUG]
 7253.11.789.155 I slot   operator(): id  0 | task 44464 | cached n_tokens = 0, memory_seq_rm [0, end)
2026-08-11 02:42:00  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 0.0%
2026-08-11 02:42:00 [DEBUG]
 7253.12.268.218 I slot   operator(): id  0 | task 44464 | cached n_tokens = 213, memory_seq_rm [213, end)
2026-08-11 02:42:00  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 50.4%
2026-08-11 02:42:01 [DEBUG]
 7253.13.106.370 I slot create_check: id  0 | task 44464 | created context checkpoint 1 of 32 (pos_min = 212, pos_max = 212, n_tokens = 213, size = 81.088 MiB)
2026-08-11 02:42:01 [DEBUG]
 7253.13.308.059 I slot   operator(): id  0 | task 44464 | cached n_tokens = 419, memory_seq_rm [419, end)
2026-08-11 02:42:01 [DEBUG]
 7253.13.308.216 I slot init_sampler: id  0 | task 44464 | init sampler, took 0.11 ms, tokens: text = 423, total = 423
2026-08-11 02:42:01  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 99.1%
2026-08-11 02:42:02 [DEBUG]
 7253.14.140.874 I slot create_check: id  0 | task 44464 | created context checkpoint 2 of 32 (pos_min = 418, pos_max = 418, n_tokens = 419, size = 81.088 MiB)
2026-08-11 02:42:02  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 100.0%
2026-08-11 02:42:05 [DEBUG]
 7253.17.342.397 I slot print_timing: id  0 | task 44464 | n_decoded =    100, tg =  31.78 t/s, tg_3s =  31.78 t/s
2026-08-11 02:42:08 [DEBUG]
 7253.20.358.043 I slot print_timing: id  0 | task 44464 | n_decoded =    190, tg =  30.84 t/s, tg_3s =  29.84 t/s
2026-08-11 02:42:09 [DEBUG]
 7253.21.124.517 I slot print_timing: id  0 | task 44464 | prompt eval time =    2414.08 ms /   423 tokens (    5.71 ms per token,   175.22 tokens per second)
7253.21.124.523 I slot print_timing: id  0 | task 44464 |        eval time =    6928.27 ms /   212 tokens (   32.68 ms per token,    30.60 tokens per second)
7253.21.124.527 I slot print_timing: id  0 | task 44464 |       total time =    9342.35 ms /   635 tokens
7253.21.124.528 I slot print_timing: id  0 | task 44464 |    graphs reused =      43808
2026-08-11 02:42:09 [DEBUG]
 7253.21.129.481 I slot      release: id  0 | task 44464 | stop processing: n_tokens = 634, truncated = 0
7253.21.129.535 I srv  update_slots: all slots are idle
2026-08-11 02:42:09  [INFO]
 [nvidia/nemotron-3-nano-4b] Finished streaming response
2026-08-11 02:42:31 [DEBUG]
 Received request: POST to /v1/chat/completions with body  {
  "model": "local-model",
  "messages": [
    {
      "role": "system",
      "content": "You are Legion V8. Expert Architect. \nUse Vector M... <Truncated in logs> ...y` to route Python runs through `pydantic_monty`!\n"
    },
    {
      "role": "user",
      "content": "Viewed parse_codebase_monty.py:1-66No, the sandbox... <Truncated in logs> ...py` to route Python runs through `pydantic_monty`!"
    },
    {
      "role": "assistant",
      "content": "I’ll refactor `execution_worker.py` to route Pytho... <Truncated in logs> ...ess.run`. Let me know if you’d like me to proceed."
    },
    {
      "role": "user",
      "content": "proceed"
    }
  ],
  "stream": true,
  "temperature": 0.3
}
2026-08-11 02:42:31  [INFO]
 [nvidia/nemotron-3-nano-4b] Running chat completion on conversation with 4 messages.
2026-08-11 02:42:31  [INFO]
 [nvidia/nemotron-3-nano-4b] Streaming response...
2026-08-11 02:42:31 [DEBUG]
 7253.42.624.281 I srv  server_strea: conv_id= (empty=1)
2026-08-11 02:42:31 [DEBUG]
 7253.42.629.108 I srv    operator(): chat format: peg-native
2026-08-11 02:42:31 [DEBUG]
 7253.42.629.412 I slot get_availabl: id  0 | task -1 | selected slot by LCP similarity, sim_best = 0.155 (> 0.100 thold), f_keep = 0.174
7253.42.629.417 I srv  get_availabl: updating prompt cache
7253.42.629.543 I srv   prompt_save:  - saving prompt with length 634, total state size = 83.882 MiB (draft: 0.000 MiB)
7253.42.629.560 W srv         alloc:  - making room for prompt cache entry, removing oldest entry (size = 245.468 MiB)
2026-08-11 02:42:31 [DEBUG]
 7253.42.701.364 I srv          load:  - looking for better prompt, base f_keep = 0.174, sim = 0.155
7253.42.701.376 I srv          load:  - found better prompt with f_keep = 0.281, sim = 0.203
2026-08-11 02:42:31 [DEBUG]
 7253.42.737.855 I srv        update:  - cache state: 19 prompts, 7800.625 MiB (limits: 8192.000 MiB, 31488 tokens, 158466 est)
7253.42.737.863 I srv        update:    - prompt 0000029C1988C1A0:    1014 tokens, checkpoints:  4,   409.910 MiB
7253.42.737.864 I srv        update:    - prompt 0000029C6CE5CA50:    4936 tokens, checkpoints:  4,   427.190 MiB
7253.42.737.865 I srv        update:    - prompt 0000029C19670FC0:    4548 tokens, checkpoints:  4,   425.480 MiB
7253.42.737.866 I srv        update:    - prompt 0000029C19670E10:   15578 tokens, checkpoints:  4,   474.078 MiB
7253.42.737.899 I srv        update:    - prompt 0000029C6BBB35A0:   31025 tokens, checkpoints:  6,   704.314 MiB
7253.42.737.903 I srv        update:    - prompt 0000029C6CE5C300:   14321 tokens, checkpoints:  4,   468.540 MiB
7253.42.737.904 I srv        update:    - prompt 0000029C6CE5CDB0:     455 tokens, checkpoints:  2,   245.270 MiB
7253.42.737.905 I srv        update:    - prompt 0000029C6CE5CE40:    2070 tokens, checkpoints:  4,   414.562 MiB
7253.42.737.907 I srv        update:    - prompt 0000029C1988C3E0:   10319 tokens, checkpoints:  5,   531.996 MiB
7253.42.737.908 I srv        update:    - prompt 0000029C6CE5C540:    7160 tokens, checkpoints:  4,   436.989 MiB
7253.42.737.909 I srv        update:    - prompt 0000029C6CE5BFA0:    5343 tokens, checkpoints:  4,   428.983 MiB
7253.42.737.911 I srv        update:    - prompt 0000029C19671560:   21017 tokens, checkpoints:  5,   579.131 MiB
7253.42.737.912 I srv        update:    - prompt 0000029C19670CF0:    5391 tokens, checkpoints:  3,   348.106 MiB
7253.42.737.913 I srv        update:    - prompt 0000029C283A0600:    3650 tokens, checkpoints:  4,   421.524 MiB
7253.42.737.914 I srv        update:    - prompt 0000029C283A0CC0:    5420 tokens, checkpoints:  3,   348.234 MiB
7253.42.737.915 I srv        update:    - prompt 0000029C283A0840:    6774 tokens, checkpoints:  2,   273.111 MiB
2026-08-11 02:42:31 [DEBUG]
 7253.42.737.916 I srv        update:    - prompt 0000029C283A0D50:   11049 tokens, checkpoints:  3,   373.035 MiB
7253.42.737.918 I srv        update:    - prompt 0000029C283A02A0:     192 tokens, checkpoints:  2,   244.111 MiB
7253.42.737.921 I srv        update:    - prompt 0000029C283A0330:     634 tokens, checkpoints:  2,   246.059 MiB
7253.42.737.923 I srv  get_availabl: prompt cache update took 108.50 ms
7253.42.738.104 I slot launch_slot_: id  0 | task -1 | sampler chain: logits -> penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
7253.42.738.134 I slot launch_slot_: id  0 | task -1 | sampler params:
 repeat_last_n = 64, repeat_penalty = 1.100, frequency_penalty = 0.000, presence_penalty = 0.000
 dry_multiplier = 0.000, dry_base = 1.750, dry_allowed_length = 2, dry_penalty_last_n = 31488
 top_k = 40, top_p = 0.950, min_p = 0.050, xtc_probability = 0.000, xtc_threshold = 0.100, typical_p = 1.000, top_n_sigma = -1.000, temp = 0.300
 mirostat = 0, mirostat_lr = 0.100, mirostat_ent = 5.000, adaptive_target = -1.000, adaptive_decay = 0.900
7253.42.738.141 I slot launch_slot_: id  0 | task 44679 | processing task, is_child = 0
7253.42.738.142 I slot process_sing: id  1 | task -1 | saving idle slot to prompt cache
7253.42.738.144 I slot prompt_clear: id  1 | task -1 | clearing prompt with 0 tokens
7253.42.738.175 I slot process_sing: id  2 | task -1 | saving idle slot to prompt cache
7253.42.738.176 I slot prompt_clear: id  2 | task -1 | clearing prompt with 0 tokens
7253.42.738.203 I slot process_sing: id  3 | task -1 | saving idle slot to prompt cache
7253.42.738.204 I slot prompt_clear: id  3 | task -1 | clearing prompt with 0 tokens
7253.42.738.240 I slot   operator(): id  0 | task 44679 | new prompt, n_ctx_slot = 31488, n_keep = 0, task.n_tokens = 711
7253.42.738.245 I slot   operator(): id  0 | task 44679 | checking checkpoint with [170, 170] against 144...
7253.42.738.245 I slot   operator(): id  0 | task 44679 | checking checkpoint with [146, 146] against 144...
7253.42.738.247 I slot   operator(): id  0 | task 44679 | forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory, see https://github.com/ggml-org/llama.cpp/pull/13194#issuecomment-2868343055)
7253.42.738.249 I slot   operator(): id  0 | task 44679 | erased invalidated context checkpoint (pos_min = 146, pos_max = 146, n_tokens = 147, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:31 [DEBUG]
 7253.42.741.448 I slot   operator(): id  0 | task 44679 | erased invalidated context checkpoint (pos_min = 170, pos_max = 170, n_tokens = 171, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:31 [DEBUG]
 7253.42.744.586 I slot   operator(): id  0 | task 44679 | cached n_tokens = 0, memory_seq_rm [0, end)
2026-08-11 02:42:31  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 0.0%
2026-08-11 02:42:31 [DEBUG]
 7253.43.181.945 I slot   operator(): id  0 | task 44679 | cached n_tokens = 195, memory_seq_rm [195, end)
2026-08-11 02:42:31  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 27.4%
2026-08-11 02:42:32 [DEBUG]
 7253.44.005.912 I slot create_check: id  0 | task 44679 | created context checkpoint 1 of 32 (pos_min = 194, pos_max = 194, n_tokens = 195, size = 81.088 MiB)
2026-08-11 02:42:32 [DEBUG]
 7253.44.218.757 I slot   operator(): id  0 | task 44679 | cached n_tokens = 438, memory_seq_rm [438, end)
2026-08-11 02:42:32  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 61.6%
2026-08-11 02:42:33 [DEBUG]
 7253.45.089.579 I slot create_check: id  0 | task 44679 | created context checkpoint 2 of 32 (pos_min = 437, pos_max = 437, n_tokens = 438, size = 81.088 MiB)
2026-08-11 02:42:33 [DEBUG]
 7253.45.357.128 I slot   operator(): id  0 | task 44679 | cached n_tokens = 698, memory_seq_rm [698, end)
2026-08-11 02:42:33  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 98.2%
2026-08-11 02:42:35 [DEBUG]
 7253.46.587.206 I slot create_check: id  0 | task 44679 | created context checkpoint 3 of 32 (pos_min = 697, pos_max = 697, n_tokens = 698, size = 81.088 MiB)
2026-08-11 02:42:35 [DEBUG]
 7253.46.642.816 I slot print_timing: id  0 | task 44679 | prompt processing, n_tokens =    707, progress = 0.99, t =   3.90 s / 181.07 tokens per second
7253.46.642.820 I slot   operator(): id  0 | task 44679 | cached n_tokens = 707, memory_seq_rm [707, end)
2026-08-11 02:42:35 [DEBUG]
 7253.46.643.004 I slot init_sampler: id  0 | task 44679 | init sampler, took 0.15 ms, tokens: text = 711, total = 711
2026-08-11 02:42:35  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 99.4%
2026-08-11 02:42:35 [DEBUG]
 7253.46.711.641 I slot create_check: id  0 | task 44679 | created context checkpoint 4 of 32 (pos_min = 706, pos_max = 706, n_tokens = 707, size = 81.088 MiB)
2026-08-11 02:42:35  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 100.0%
2026-08-11 02:42:38 [DEBUG]
 7253.49.801.035 I slot print_timing: id  0 | task 44679 | n_decoded =    100, tg =  32.91 t/s, tg_3s =  32.91 t/s
2026-08-11 02:42:41 [DEBUG]
 7253.52.815.157 I slot print_timing: id  0 | task 44679 | n_decoded =    197, tg =  32.55 t/s, tg_3s =  32.18 t/s
2026-08-11 02:42:41 [DEBUG]
 7253.53.397.915 I slot print_timing: id  0 | task 44679 | prompt eval time =    4024.45 ms /   711 tokens (    5.66 ms per token,   176.67 tokens per second)
7253.53.397.921 I slot print_timing: id  0 | task 44679 |        eval time =    6635.20 ms /   214 tokens (   31.01 ms per token,    32.25 tokens per second)
7253.53.397.922 I slot print_timing: id  0 | task 44679 |       total time =   10659.65 ms /   925 tokens
7253.53.397.923 I slot print_timing: id  0 | task 44679 |    graphs reused =      44019
7253.53.397.986 I slot      release: id  0 | task 44679 | stop processing: n_tokens = 924, truncated = 0
7253.53.398.048 I
2026-08-11 02:42:41 [DEBUG]
 srv  update_slots: all slots are idle
2026-08-11 02:42:41  [INFO]
 [nvidia/nemotron-3-nano-4b] Finished streaming response
2026-08-11 02:42:51 [DEBUG]
 Received request: POST to /v1/chat/completions with body  {
  "model": "local-model",
  "messages": [
    {
      "role": "system",
      "content": "You are Legion V8. Expert Architect. \nUse Vector M... <Truncated in logs> ...)\n<<<END>>>\n<<<EXECUTE: cmd>>> python test_val.py\n"
    },
    {
      "role": "assistant",
      "content": "I’ll refactor`execution_worker.py`to route Pytho... <Truncated in logs> ...ess.run`. Let me know if you’d like me to proceed."
    },
    {
      "role": "user",
      "content": "proceed"
    },
    {
      "role": "assistant",
      "content": "Refactored `execution_worker.py` now routes Python... <Truncated in logs> ..._monty` sandbox instead of using `subprocess.run`."
    },
    {
      "role": "user",
      "content": "status"
    }
  ],
  "stream": true,
  "temperature": 0.3
}
2026-08-11 02:42:51  [INFO]
 [nvidia/nemotron-3-nano-4b] Running chat completion on conversation with 5 messages.
2026-08-11 02:42:51  [INFO]
 [nvidia/nemotron-3-nano-4b] Streaming response...
2026-08-11 02:42:51 [DEBUG]
 7254.02.485.282 I srv  server_strea: conv_id= (empty=1)
2026-08-11 02:42:51 [DEBUG]
 7254.02.488.435 I srv    operator(): chat format: peg-native
2026-08-11 02:42:51 [DEBUG]
 7254.02.488.725 I slot get_availabl: id  0 | task -1 | selected slot by LCP similarity, sim_best = 0.320 (> 0.100 thold), f_keep = 0.119
7254.02.488.730 I srv  get_availabl: updating prompt cache
2026-08-11 02:42:51 [DEBUG]
 7254.02.488.877 I srv   prompt_save:  - saving prompt with length 924, total state size = 85.160 MiB (draft: 0.000 MiB)
7254.02.488.891 W srv         alloc:  - making room for prompt cache entry, removing oldest entry (size = 409.910 MiB)
2026-08-11 02:42:51 [DEBUG]
 7254.02.588.247 I srv          load:  - looking for better prompt, base f_keep = 0.119, sim = 0.320
7254.02.588.265 I srv        update:  - cache state: 19 prompts, 7800.229 MiB (limits: 8192.000 MiB, 31488 tokens, 158380 est)
7254.02.588.267 I srv        update:    - prompt 0000029C6CE5CA50:    4936 tokens, checkpoints:  4,   427.190 MiB
7254.02.588.269 I srv        update:    - prompt 0000029C19670FC0:    4548 tokens, checkpoints:  4,   425.480 MiB
7254.02.588.278 I srv        update:    - prompt 0000029C19670E10:   15578 tokens, checkpoints:  4,   474.078 MiB
7254.02.588.280 I srv        update:    - prompt 0000029C6BBB35A0:   31025 tokens, checkpoints:  6,   704.314 MiB
7254.02.588.281 I srv        update:    - prompt 0000029C6CE5C300:   14321 tokens, checkpoints:  4,   468.540 MiB
7254.02.588.282 I srv        update:    - prompt 0000029C6CE5CDB0:     455 tokens, checkpoints:  2,   245.270 MiB
7254.02.588.284 I srv        update:    - prompt 0000029C6CE5CE40:    2070 tokens, checkpoints:  4,   414.562 MiB
7254.02.588.285 I srv        update:    - prompt 0000029C1988C3E0:   10319 tokens, checkpoints:  5,   531.996 MiB
7254.02.588.286 I srv        update:    - prompt 0000029C6CE5C540:    7160 tokens, checkpoints:  4,   436.989 MiB
7254.02.588.287 I srv        update:    - prompt 0000029C6CE5BFA0:    5343 tokens, checkpoints:  4,   428.983 MiB
7254.02.588.288 I srv        update:    - prompt 0000029C19671560:   21017 tokens, checkpoints:  5,   579.131 MiB
7254.02.588.289 I srv        update:    - prompt 0000029C19670CF0:    5391 tokens, checkpoints:  3,   348.106 MiB
7254.02.588.291 I srv        update:    - prompt 0000029C283A0600:    3650 tokens, checkpoints:  4,   421.524 MiB
7254.02.588.292 I srv        update:    - prompt 0000029C283A0CC0:    5420 tokens, checkpoints:  3,   348.234 MiB
7254.02.588.293 I srv        update:    - prompt 0000029C283A0840:    6774 tokens, checkpoints:  2,   273.111 MiB
7254.02.588.296 I srv        update:    - prompt 0000029C283A0D50:   11049 tokens, checkpoints:  3,   373.035 MiB
7254.02.588.298 I srv        update:    - prompt 0000029C283A02A0:     192 tokens, checkpoints:  2,   244.111 MiB
7254.02.588.299 I srv        update:    - prompt 0000029C283A0330:     634 tokens, checkpoints:  2,   246.059 MiB
7254.02.588.300 I srv        update:    - prompt 0000029C283A03C0:     924 tokens, checkpoints:  4,   409.513 MiB
7254.02.588.302 I srv  get_availabl: prompt cache update took 99.57 ms
2026-08-11 02:42:51 [DEBUG]
 7254.02.588.528 I slot launch_slot_: id  0 | task -1 | sampler chain: logits -> penalties -> ?dry -> ?top-n-sigma -> top-k -> ?typical -> top-p -> min-p -> ?xtc -> temp-ext -> dist
7254.02.588.544 I slot launch_slot_: id  0 | task -1 | sampler params:
 repeat_last_n = 64, repeat_penalty = 1.100, frequency_penalty = 0.000, presence_penalty = 0.000
 dry_multiplier = 0.000, dry_base = 1.750, dry_allowed_length = 2, dry_penalty_last_n = 31488
 top_k = 40, top_p = 0.950, min_p = 0.050, xtc_probability = 0.000, xtc_threshold = 0.100, typical_p = 1.000, top_n_sigma = -1.000, temp = 0.300
 mirostat = 0, mirostat_lr = 0.100, mirostat_ent = 5.000, adaptive_target = -1.000, adaptive_decay = 0.900
7254.02.588.550 I slot launch_slot_: id  0 | task 44898 | processing task, is_child = 0
7254.02.588.551 I slot process_sing: id  1 | task -1 | saving idle slot to prompt cache
7254.02.588.552 I slot prompt_clear: id  1 | task -1 | clearing prompt with 0 tokens
7254.02.588.589 I slot process_sing: id  2 | task -1 | saving idle slot to prompt cache
7254.02.588.591 I slot prompt_clear: id  2 | task -1 | clearing prompt with 0 tokens
7254.02.588.621 I slot process_sing: id  3 | task -1 | saving idle slot to prompt cache
7254.02.588.623 I slot prompt_clear: id  3 | task -1 | clearing prompt with 0 tokens
7254.02.588.662 I slot   operator(): id  0 | task 44898 | new prompt, n_ctx_slot = 31488, n_keep = 0, task.n_tokens = 344
7254.02.588.667 I slot   operator(): id  0 | task 44898 | checking checkpoint with [706, 706] against 110...
7254.02.588.668 I slot   operator(): id  0 | task 44898 | checking checkpoint with [697, 697] against 110...
7254.02.588.669 I slot   operator(): id  0 | task 44898 | checking checkpoint with [437, 437] against 110...
7254.02.588.669 I slot   operator(): id  0 | task 44898 | checking checkpoint with [194, 194] against 110...
7254.02.588.671 I slot   operator(): id  0 | task 44898 | forcing full prompt re-processing due to lack of cache data (likely due to SWA or hybrid/recurrent memory, see https://github.com/ggml-org/llama.cpp/pull/13194#issuecomment-2868343055)
7254.02.588.674 I slot   operator(): id  0 | task 44898 | erased invalidated context checkpoint (pos_min = 194, pos_max = 194, n_tokens = 195, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:51 [DEBUG]
 7254.02.592.508 I slot   operator(): id  0 | task 44898 | erased invalidated context checkpoint (pos_min = 437, pos_max = 437, n_tokens = 438, n_swa = 0, pos_next = 0, size = 81.088 MiB)
7254.02.595.927 I slot   operator(): id  0 | task 44898 | erased invalidated context checkpoint (pos_min = 697, pos_max = 697, n_tokens = 698, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:51 [DEBUG]
 7254.02.599.343 I slot   operator(): id  0 | task 44898 | erased invalidated context checkpoint (pos_min = 706, pos_max = 706, n_tokens = 707, n_swa = 0, pos_next = 0, size = 81.088 MiB)
2026-08-11 02:42:51 [DEBUG]
 7254.02.602.772 I slot   operator(): id  0 | task 44898 | cached n_tokens = 0, memory_seq_rm [0, end)
2026-08-11 02:42:51  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 0.0%
2026-08-11 02:42:51 [DEBUG]
 7254.03.127.410 I slot   operator(): id  0 | task 44898 | cached n_tokens = 281, memory_seq_rm [281, end)
2026-08-11 02:42:51  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 81.7%
2026-08-11 02:42:52 [DEBUG]
 7254.04.365.816 I slot create_check: id  0 | task 44898 | created context checkpoint 1 of 32 (pos_min = 280, pos_max = 280, n_tokens = 281, size = 81.088 MiB)
2026-08-11 02:42:53 [DEBUG]
 7254.04.451.784 I slot   operator(): id  0 | task 44898 | cached n_tokens = 332, memory_seq_rm [332, end)
2026-08-11 02:42:53  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 96.5%
2026-08-11 02:42:53 [DEBUG]
 7254.04.673.093 I slot create_check: id  0 | task 44898 | created context checkpoint 2 of 32 (pos_min = 331, pos_max = 331, n_tokens = 332, size = 81.088 MiB)
2026-08-11 02:42:53 [DEBUG]
 7254.04.719.220 I slot   operator(): id  0 | task 44898 | cached n_tokens = 340, memory_seq_rm [340, end)
2026-08-11 02:42:53 [DEBUG]
 7254.04.719.369 I slot init_sampler: id  0 | task 44898 | init sampler, took 0.09 ms, tokens: text = 344, total = 344
2026-08-11 02:42:53  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 98.8%
2026-08-11 02:42:53 [DEBUG]
 7254.04.754.671 I slot create_check: id  0 | task 44898 | created context checkpoint 3 of 32 (pos_min = 339, pos_max = 339, n_tokens = 340, size = 81.088 MiB)
2026-08-11 02:42:53  [INFO]
 [nvidia/nemotron-3-nano-4b] Prompt processing progress: 100.0%
2026-08-11 02:42:56 [DEBUG]
 7254.07.910.110 I slot print_timing: id  0 | task 44898 | prompt eval time =    2219.92 ms /   344 tokens (    6.45 ms per token,   154.96 tokens per second)
7254.07.910.117 I slot print_timing: id  0 | task 44898 |        eval time =    3101.51 ms /    94 tokens (   32.99 ms per token,    30.31 tokens per second)
7254.07.910.119 I slot print_timing: id  0 | task 44898 |       total time =    5321.42 ms /   438 tokens
7254.07.910.120 I slot print_timing: id  0 | task 44898 |    graphs reused =      44111
7254.07.910.178 I slot      release: id  0 | task 44898 | stop processing: n_tokens = 437, truncated = 0
7254.07.910.204 I srv  update_slots: all slots are idle
2026-08-11 02:42:56  [INFO]
 [nvidia/nemotron-3-nano-4b] Finished streaming response
