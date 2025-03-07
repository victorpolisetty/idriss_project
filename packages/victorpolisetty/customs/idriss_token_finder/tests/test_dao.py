"""Test DAOs."""

import sys
import random
import shutil
from pathlib import Path

import pytest


DAOS_PATH = Path(__file__).parent.parent / "daos"
sys.path.append(str(DAOS_PATH.parent))

from daos.analyze_request_dao import AnalyzeRequestDAO

@pytest.fixture(scope="module")
def _test_context():
    """Setup and teardown for DAO tests."""
    data_file = DAOS_PATH / "aggregated_data.json"
    backup_file = data_file.with_suffix(".json.bak")

    if data_file.exists():
        shutil.copy2(data_file, backup_file)
    else:
        msg = f"Data file {data_file} not found"
        raise FileNotFoundError(msg)

    yield

    if backup_file.exists():
        shutil.move(backup_file, data_file)


@pytest.fixture(params=[
    (AnalyzeRequestDAO,
        {
            "count": 42,
            "engagement": "STRING_VALUE",
            "max_results": 42,
            "query": "STRING_VALUE",
            "text": "STRING_VALUE",
            "walletAddress": "STRING_VALUE"
}),
], scope="module")
def dao_and_dummy_data(request):
    """Return a DAO and dummy data."""
    dao_type, dummy_data = request.param
    dao = dao_type()
    return dao, dummy_data


@pytest.mark.usefixtures("_test_context")
class TestDAOs:
    """Test suite for DAO operations."""
    def test_insert(self, dao_and_dummy_data):
        """Test insert operation."""
        dao, dummy_data = dao_and_dummy_data
        initial_count = len(dao.get_all())
        dao.insert(dummy_data)
        all_data = dao.get_all()
        assert len(all_data) == initial_count + 1, "Insert did not increase count"
        assert any(item == dummy_data for item in all_data.values()), "Inserted item not found"

    def test_get_all(self, dao_and_dummy_data):
        """Test get_all operation."""
        dao, dummy_data = dao_and_dummy_data
        initial_count = len(dao.get_all())
        dao.insert(dummy_data)
        result = dao.get_all()
        assert isinstance(result, dict), "get_all did not return a dict"
        assert len(result) == initial_count + 1, (
            f"Unexpected number of items. Expected {initial_count + 1}, got {len(result)}"
        )
        assert any(
            all(str(item.get(k)) == str(v) for k, v in dummy_data.items())
            for item in result.values()
        ), "Inserted item not found in get_all"

    def test_get_by_id(self, dao_and_dummy_data):
        """Test get_by_id operation."""
        dao, dummy_data = dao_and_dummy_data
        dao.insert(dummy_data)
        all_items = dao.get_all()
        if not all_items:
            pytest.fail(f"No items found in the {dao.__class__.__name__} to test get_by_id")

        random_id = random.choice(list(all_items.keys()))  # noqa: S311
        result = dao.get_by_id(random_id)
        assert result == all_items[random_id], f"get_by_id returned incorrect data for id {random_id}"

        non_existent_id = str(max(map(int, all_items.keys())) + 1)
        assert dao.get_by_id(non_existent_id) is None, (
            f"get_by_id should return None for non-existent id {non_existent_id}"
        )

    def test_update(self, dao_and_dummy_data):
        """Test update operation."""
        dao, dummy_data = dao_and_dummy_data
        dao.insert(dummy_data)
        all_items = dao.get_all()
        update_key = random.choice(list(all_items.keys()))  # noqa: S311
        update_data = dummy_data.copy()

        result = dao.update(update_key, **update_data)
        assert result is not None, "Update returned None"

        updated_item = dao.get_by_id(update_key)
        assert updated_item == update_data, "Updated item does not match"

    def test_delete(self, dao_and_dummy_data):
        """Test delete operation."""
        dao, dummy_data = dao_and_dummy_data
        dao.insert(dummy_data)
        all_items = dao.get_all()
        initial_count = len(all_items)
        delete_key = random.choice(list(all_items.keys()))  # noqa: S311

        assert dao.delete(delete_key), "Delete operation did not return True"

        all_data_after_delete = dao.get_all()
        assert delete_key not in all_data_after_delete, "Deleted item still present"
        assert len(all_data_after_delete) == initial_count - 1, "Count did not decrease after delete"
        assert dao.get_by_id(delete_key) is None, "Deleted item can still be retrieved"


if __name__ == "__main__":
    pytest.main()
