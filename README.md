
# SQL Copilot with OpenAI

This project allows users to:

1. Upload a CSV file and dynamically create or update a SQLite table based on the content.
2. Interact with a command-line copilot that uses OpenAI to convert natural language queries into SQL statements and execute them on the imported data.

---

## Features

-  Automatically creates or updates SQLite tables from CSV files
-  Supports schema extension if new columns appear in new CSVs
-  Uses OpenAI GPT-4o-mini to convert natural language into SQL
-  Interactive shell: input natural language → get SQL → run it → see results


## Prerequisites

- Python 3.9
- OpenAI SDK (`pip install openai`)
- Set your OpenAI API key as an environment variable in file '.env':
  
```bash
export API_KEY="sk-..."
```

---

## Usage

1. Place your CSV file (e.g., `example.csv`) in the same directory as `main.py`.

2. Run the script:

```bash
python main.py
```

3. After table creation and data insertion, enter natural language queries like:

- 查询工资大于6000的员工
- 查询名字中带A的人
- Show all employees older than 30 in the Engineering department

4. Type `exit` or `quit` to stop the session.

---

## File Structure

```
├── main.py         # Main program entry
├── example.csv     # Your data file
├── example.db      # Auto-generated SQLite database
```

---

## Sample Data (example.csv)

Included in the repo

---






