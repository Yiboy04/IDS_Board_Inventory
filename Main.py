import os
import json
import argparse
import shutil
from typing import List, Dict, Optional


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")


def _get_data_dir() -> str:
	# Read data_dir from config.json if present; default to ./data
	try:
		if os.path.exists(CONFIG_FILE):
			with open(CONFIG_FILE, "r", encoding="utf-8") as f:
				cfg = json.load(f)
				dd = cfg.get("data_dir")
				if isinstance(dd, str) and dd.strip():
					return dd
	except Exception:
		pass
	return os.path.join(os.path.dirname(__file__), "data")


DATA_DIR = _get_data_dir()
NOTE_FILE = os.path.join(DATA_DIR, "boards_note.jsonl")
EMP_FILE = os.path.join(DATA_DIR, "employees_note.jsonl")
PICTURES_DIR = os.path.join(DATA_DIR, "pictures")


def _ensure_storage() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(NOTE_FILE):
		# Create empty file
		with open(NOTE_FILE, "w", encoding="utf-8") as f:
			pass
	# Ensure pictures directory exists
	os.makedirs(PICTURES_DIR, exist_ok=True)


def _load_boards() -> List[Dict]:
	_ensure_storage()
	boards: List[Dict] = []
	with open(NOTE_FILE, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			try:
				boards.append(json.loads(line))
			except json.JSONDecodeError:
				# Skip malformed lines but keep the file intact
				continue
	return boards


def _write_boards(boards: List[Dict]) -> None:
	_ensure_storage()
	with open(NOTE_FILE, "w", encoding="utf-8") as f:
		for b in boards:
			f.write(json.dumps(b, ensure_ascii=False) + "\n")


def _ensure_employee_storage() -> None:
	os.makedirs(DATA_DIR, exist_ok=True)
	if not os.path.exists(EMP_FILE):
		with open(EMP_FILE, "w", encoding="utf-8") as f:
			pass


def _load_employees() -> List[Dict]:
	_ensure_employee_storage()
	emps: List[Dict] = []
	with open(EMP_FILE, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			try:
				emps.append(json.loads(line))
			except json.JSONDecodeError:
				continue
	return emps


def _write_employees(emps: List[Dict]) -> None:
	_ensure_employee_storage()
	with open(EMP_FILE, "w", encoding="utf-8") as f:
		for e in emps:
			f.write(json.dumps(e, ensure_ascii=False) + "\n")


def find_employee(username: str) -> Optional[Dict]:
	for e in _load_employees():
		if str(e.get("username")) == str(username):
			return e
	return None


def add_or_update_employee(username: str, password: str) -> Dict:
	if not username or not password:
		raise ValueError("Username and password are required")
	if username == "admin":
		raise ValueError("Cannot create or modify the built-in admin user")
	emps = _load_employees()
	# remove existing with same username
	emps = [e for e in emps if str(e.get("username")) != str(username)]
	new_emp = {"username": username, "password": password}
	emps.append(new_emp)
	_write_employees(emps)
	return new_emp


def delete_employee(username: str) -> bool:
	if username == "admin":
		return False
	emps = _load_employees()
	new_emps = [e for e in emps if str(e.get("username")) != str(username)]
	if len(new_emps) == len(emps):
		return False
	_write_employees(new_emps)
	return True


def list_employees() -> List[Dict]:
	return _load_employees()


def find_board_by_id(board_id: str) -> Optional[Dict]:
	for b in _load_boards():
		if str(b.get("board_id")) == str(board_id):
			return b
	return None


def add_board(
	board_id: str,
	name: str,
	ic: str,
	dc: str,
	size: str,
	module_number: Optional[str] = None,
	pixel: Optional[str] = None,
	board_code: Optional[str] = None,
	running_no: Optional[str] = None,
	date_request: Optional[str] = None,
	do_date: Optional[str] = None,
	date_repair: Optional[str] = None,
	before_photo: Optional[str] = None,
	after_photo: Optional[str] = None,
	urgency: bool = False,
	issues: Optional[Dict] = None,
	created_by: Optional[str] = None,
) -> Dict:
	if not all([board_id, name, ic, dc, size]):
		raise ValueError("All fields are required: board_id, name, ic, dc, size")
	boards = _load_boards()
	if any(str(b.get("board_id")) == str(board_id) for b in boards):
		raise ValueError(f"Board with ID '{board_id}' already exists")
	# Prepare photo paths: accept either source file paths or already-stored paths under pictures
	def _store_photo(src_path: Optional[str], tag: str) -> Optional[str]:
		if not src_path:
			return None
		try:
			# If already within PICTURES_DIR, keep as relative path
			abs_src = os.path.abspath(src_path)
			pics_abs = os.path.abspath(PICTURES_DIR)
			if abs_src.startswith(pics_abs):
				rel = os.path.relpath(abs_src, DATA_DIR)
				return rel.replace("\\", "/")
			# Otherwise, copy into pictures dir
			_, ext = os.path.splitext(src_path)
			ext = (ext or "").lower()
			dest_name = f"{board_id}_{tag}{ext}"
			dest_abs = os.path.join(PICTURES_DIR, dest_name)
			shutil.copy2(src_path, dest_abs)
			rel = os.path.relpath(dest_abs, DATA_DIR)
			return rel.replace("\\", "/")
		except Exception:
			return None

	before_rel = _store_photo(before_photo, "before")
	after_rel = _store_photo(after_photo, "after")

	board = {
		"board_id": str(board_id),
		"name": name,
		"ic": ic,
		"dc": dc,
		"size": size,
		"module_number": module_number,
		"pixel": pixel,
		"board_code": board_code,
		"running_no": running_no,
		"date_request": date_request,
		"do_date": do_date,
		"date_repair": date_repair,
		"before_photo": before_rel,
		"after_photo": after_rel,
		"urgency": bool(urgency),
		"issues": issues or {},
		"created_by": created_by,
	}
	boards.append(board)
	_write_boards(boards)
	return board


def list_boards() -> List[Dict]:
	return _load_boards()


def delete_board(board_id: str) -> bool:
	boards = _load_boards()
	new_boards = [b for b in boards if str(b.get("board_id")) != str(board_id)]
	if len(new_boards) == len(boards):
		return False
	_write_boards(new_boards)
	return True


def show_board(board_id: str) -> Optional[Dict]:
	return find_board_by_id(board_id)


def _print_board(board: Dict) -> None:
	print(
		f"ID: {board.get('board_id')} | Name: {board.get('name')} | "
		f"IC: {board.get('ic')} | DC: {board.get('dc')} | Size: {board.get('size')}"
	)


def main():
	parser = argparse.ArgumentParser(
		description="LED Board note storage (JSONL)."
	)
	subparsers = parser.add_subparsers(dest="command")

	# add command
	p_add = subparsers.add_parser("add", help="Add a new board")
	p_add.add_argument("--id", required=True, help="Board ID")
	p_add.add_argument("--name", required=True, help="Board name")
	p_add.add_argument("--ic", required=True, help="Board IC (e.g., SM1627P)")
	p_add.add_argument("--dc", required=True, help="Board DC (e.g., 74HC 368)")
	p_add.add_argument("--size", required=True, help="Board size (free-form)")

	# list command
	subparsers.add_parser("list", help="List all boards")

	# show command
	p_show = subparsers.add_parser("show", help="Show a board by ID")
	p_show.add_argument("--id", required=True, help="Board ID to show")

	# delete command
	p_del = subparsers.add_parser("delete", help="Delete a board by ID")
	p_del.add_argument("--id", required=True, help="Board ID to delete")

	# gui command
	subparsers.add_parser("gui", help="Launch the GUI application")

	# interactive command (text menu)
	subparsers.add_parser("interactive", help="Run interactive text menu")

	args = parser.parse_args()

	# If no subcommand provided, launch GUI by default.
	if args.command is None:
		# Import GUI module lazily and pass required functions to avoid circular imports
		from login_gui import run_gui as _run_gui
		return _run_gui(
			list_boards=list_boards,
			add_board=add_board,
			delete_board=delete_board,
			find_board_by_id=find_board_by_id,
			find_employee=find_employee,
			list_employees=list_employees,
			add_or_update_employee=add_or_update_employee,
			delete_employee=delete_employee,
		)

	try:
		if args.command == "add":
			board = add_board(args.id, args.name, args.ic, args.dc, args.size)
			print("Added board:")
			_print_board(board)
		elif args.command == "list":
			boards = list_boards()
			if not boards:
				print("No boards saved yet.")
			else:
				for b in boards:
					_print_board(b)
		elif args.command == "show":
			board = show_board(args.id)
			if not board:
				print(f"Board ID '{args.id}' not found.")
			else:
				_print_board(board)
		elif args.command == "delete":
			ok = delete_board(args.id)
			if ok:
				print(f"Deleted board ID '{args.id}'.")
			else:
				print(f"Board ID '{args.id}' not found.")
		elif args.command == "gui":
			from login_gui import run_gui as _run_gui
			_run_gui(
				list_boards=list_boards,
				add_board=add_board,
				delete_board=delete_board,
				find_board_by_id=find_board_by_id,
				find_employee=find_employee,
				list_employees=list_employees,
				add_or_update_employee=add_or_update_employee,
				delete_employee=delete_employee,
			)
		elif args.command == "interactive":
			run_interactive()
	except Exception as e:
		print(f"Error: {e}")





def run_interactive():
	while True:
		print("\nLED Board Manager")
		print("1) List boards")
		print("2) Add board")
		print("3) Show board")
		print("4) Delete board")
		print("5) Exit")
		choice = input("Select an option (1-5): ").strip()

		if choice == "1":
			boards = list_boards()
			if not boards:
				print("No boards saved yet.")
			else:
				for b in boards:
					_print_board(b)
		elif choice == "2":
			board_id = input("Board ID: ").strip()
			name = input("Board name: ").strip()
			ic = input("Board IC (e.g., SM1627P): ").strip()
			dc = input("Board DC (e.g., 74HC 368): ").strip()
			size = input("Board size: ").strip()
			try:
				board = add_board(board_id, name, ic, dc, size)
				print("Added board:")
				_print_board(board)
			except Exception as e:
				print(f"Error: {e}")
		elif choice == "3":
			board_id = input("Board ID to show: ").strip()
			b = show_board(board_id)
			if not b:
				print("Not found.")
			else:
				_print_board(b)
		elif choice == "4":
			board_id = input("Board ID to delete: ").strip()
			ok = delete_board(board_id)
			print("Deleted." if ok else "Not found.")
		elif choice == "5":
			print("Goodbye.")
			break
		else:
			print("Invalid choice. Please select 1-5.")


if __name__ == "__main__":
	main()
