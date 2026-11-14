from agent.ids import is_run_id, new_run_id


def test_new_ids_are_well_formed_and_unique():
    ids = {new_run_id("error_prone") for _ in range(50)}
    assert len(ids) == 50 and all(is_run_id(i) for i in ids)


def test_recorded_demo_ids_still_match():
    assert is_run_id("20261014T113651Z-error_prone-a9102d")


def test_paths_and_junk_are_not_run_ids():
    for text in ["..", "../logs", "20261014T113651Z-error_prone-a9102d/../x", "", "abc"]:
        assert not is_run_id(text)
