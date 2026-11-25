| Bug | Expected signal | SimUX persona | Keyboard sweep | axe-core | Single-prompt LLM |
| --- | --- | --- | --- | --- | --- |
| B1 | `data_loss_on_error` | 1/5 (missed) | no | no | no: label |
| B2 | `error_not_identified` | 1/5 (missed) | no | no | no |
| B3 | `error_not_actionable` | 1/5 (missed) | no | no | no |
| B4 | `duplicate_submission` | 1/5 (missed) | no | no | no |
| B5 | `destructive_without_confirm` | 5/5 (found, baseline too) | no | no | no |
| B6 | `redundant_entry` | 5/5 (found, baseline too) | no | no | yes: redundant_entry |
| B7 | `recall_required` | 5/5 (found, attributed) | no | no | no |
| B8 | `lost_location` | 0/5 (missed) | no | no | no: label, redundant_entry |
| B9 | `no_progress_indicator` | 5/5 (found, baseline too) | no | no | no: destructive_without_confirm |
| B10 | `label_unintelligible` | 0/5 (missed) | no | no | no: duplicate_submission |
| B11 | `instruction_unintelligible` | 5/5 (found, attributed) | no | no | yes: instruction_unintelligible, recall_required |
| B12 | `system_language` | 5/5 (found, baseline too) | no | no | no |
| B13 | `status_not_announced` | 1/1 (found, no baseline run) | no | no | no |
| B14 | `non_semantic_control` | 1/1 (found, no baseline run) | yes: unreachable_control | no | no: recall_required |
| B15 | `no_structure` | 1/1 (found, no baseline run) | no | yes: landmark-one-main, page-has-heading-one | no |
| B16 | `focus_order_illogical` | 0/1 (missed) | no | yes: tabindex | no |
| B17 | `focus_not_visible` | 1/1 (found, no baseline run) | no | no | no |
| B18 | `mis_tap_consequence` | 1/1 (found, no baseline run) | no | no | no |
| B19 | `target_too_small` | 1/1 (found, no baseline run) | no | no | no: destructive_without_confirm |
| B20 | `reflow_failure` | 1/1 (found, no baseline run) | no | no | no |
| B21 | `focus_obscured` | 1/1 (found, no baseline run) | no | no | no: label |
| B22 | `text_clipped` | 1/1 (found, no baseline run) | no | no | no: no_way_back |
| B23 | `key_info_buried` | 1/1 (found, no baseline run) | no | no | no |
| B24 | `cta_below_fold` | 1/1 (found, no baseline run) | no | no | no: image-alt |
| B25 | `headings_not_descriptive` | 1/1 (found, no baseline run) | no | no | no: recall_required |
| B26 | `timeout_no_warning` | 0/1 (missed) | no | no | no |
| B27 | `state_lost_on_reload` | 0/1 (missed) | no | no | no |
| B28 | `no_loading_feedback` | 1/1 (found, no baseline run) | no | no | no |
| B29 | `network_failure_silent` | 1/1 (found, no baseline run) | no | no | no: duplicate_submission, error_not_identified |
| B30 | `help_unreachable` | 1/1 (found, no baseline run) | no | no | no |
| B31 | `help_inconsistent` | 1/1 (found, no baseline run) | no | no | no |
| B32 | `inconsistent_identification` | 1/1 (found, no baseline run) | no | no | no |
| B33 | `inconsistent_navigation` | 1/1 (found, no baseline run) | no | no | no |
| B34 | `no_enter_submit` | 0/1 (missed) | no | no | no: duplicate_submission |
| B35 | `no_bulk_action` | 1/1 (found, no baseline run) | no | no | no: no_way_back, recall_required |
| B36 | `data_lost_on_timeout` | 1/1 (found, no baseline run) | no | no | no |
| SB-01 | `image-alt` | not run | no | yes: image-alt | yes: image-alt |
| SB-02 | `button-name` | not run | no | yes: button-name | yes: button-name |
| SB-03 | `label` | not run | no | yes: label | yes: label |
| SB-04 | `keyboard_trap` | not run | yes: keyboard_trap | no | no |
| SB-05 | `unreachable_control` | not run | yes: unreachable_control | no | no: button-name |
| **Detected** | | 26/41 | 3/41 | 5/41 | 5/41 |
