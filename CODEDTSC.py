import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
import matplotlib.pyplot as plt
import mplcursors
from datetime import datetime

def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="asmita",  
        password="12345678",  
        database="football_data"  
    )


def fetch_clubs():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM club WHERE name IS NOT NULL")
    clubs = [row[0] for row in cursor.fetchall()]
    conn.close()
    return clubs

def fetch_nationalities():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT country_of_citizenship FROM player WHERE country_of_citizenship IS NOT NULL")
    nations = [row[0] for row in cursor.fetchall()]
    conn.close()
    return nations

def fetch_seasons():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT YEAR(date) FROM appearance WHERE date IS NOT NULL ORDER BY YEAR(date)")
    seasons = [str(row[0]) for row in cursor.fetchall()]
    conn.close()
    return seasons

def show_top_performers_by_goals():
    try:
        n = int(entry_top_n_goals.get())
        if n <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid input", "Enter a valid positive number for Top N players.")
        return

    selected_club = club_choice.get()
    selected_season = season_choice.get()
    selected_nat = nationality_choice.get()

    query = """
        SELECT a.player_name,
               SUM(a.goals) AS total_goals,
               p.country_of_citizenship,
               c.name AS club_name,
               YEAR(a.date) AS season
        FROM appearance a
        LEFT JOIN player p ON a.player_id = p.player_id
        LEFT JOIN club c ON a.player_club_id = c.club_id
        WHERE a.goals IS NOT NULL
    """

    filters = []
    if selected_club != "All":
        filters.append(f"c.name = '{selected_club}'")
    if selected_season != "All":
        filters.append(f"YEAR(a.date) = {selected_season}")
    if selected_nat != "All":
        filters.append(f"p.country_of_citizenship = '{selected_nat}'")

    if filters:
        query += " AND " + " AND ".join(filters)

    query += f"""
        GROUP BY a.player_name, p.country_of_citizenship, c.name, season
        ORDER BY total_goals DESC
        LIMIT {n}
    """

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    goal_result_box.delete("1.0", tk.END)
    if not results:
        goal_result_box.insert(tk.END, "No results found.")
    else:
        for row in results:
            goal_result_box.insert(tk.END, f"Name: {row[0]}, Goals: {row[1]}, Nationality: {row[2]}, Club: {row[3]}, Season: {row[4]}\n")

def show_top_aggressive_players():
    try:
        n = int(entry_top_n_aggressive.get())
        if n <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a positive number for Top N.")
        return

    card_type = card_choice.get()

    query = f"""
        SELECT
            a.player_name,
            SUM(a.{card_type}) AS total_cards,
            p.country_of_citizenship,
            c.name AS club_name,
            YEAR(a.date) AS season
        FROM appearance a
        JOIN player p ON a.player_id = p.player_id
        JOIN club c ON a.player_club_id = c.club_id
        WHERE a.{card_type} IS NOT NULL
        GROUP BY a.player_name, p.country_of_citizenship, c.name, season
        ORDER BY total_cards DESC
        LIMIT {n}
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        aggressive_result_box.delete("1.0", tk.END)
        if not results:
            aggressive_result_box.insert(tk.END, "No data found.\n")
        else:
            for row in results:
                aggressive_result_box.insert(tk.END, f"Name: {row[0]}, Total Cards: {row[1]}, Nationality: {row[2]}, Club: {row[3]}, Season: {row[4]}\n")

    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))

def show_transfer_flowchart():
    player_name = entry_player_name.get().strip()
    if not player_name:
        messagebox.showwarning("Input Error", "Please enter a player name.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        query = """
        SELECT from_club_name, to_club_name, transfer_season
        FROM transfers
        WHERE player_name LIKE %s
        ORDER BY transfer_season
        """
        cursor.execute(query, (f"%{player_name}%",))
        rows = cursor.fetchall()
        if not rows:
            messagebox.showinfo("No Data", f"No transfer data for '{player_name}'")
            return

        flowchart_canvas.delete("all")
        x, y = 10, 20
        for i, (from_club, to_club, season) in enumerate(rows):
            text = f"{from_club or 'Unknown'} → {to_club or 'Unknown'} ({season})"
            flowchart_canvas.create_text(x, y + i * 30, text=text, anchor="nw", font=("Arial", 12))

        flowchart_canvas.configure(scrollregion=flowchart_canvas.bbox("all"))

    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", str(err))
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def search_player_details():
    player_name = entry_name.get()
    if not player_name:
        messagebox.showerror("Error", "Please enter a player name.")
        return

    query = f"""
        SELECT
            p.name AS player_name,
            p.position,
            p.sub_position,
            p.country_of_citizenship,
            p.country_of_birth,
            p.city_of_birth,
            c.name AS current_club
        FROM
            player p
        LEFT JOIN
            club c ON p.current_club_id = c.club_id
        WHERE
            p.name LIKE %s
    """

    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(query, (f"%{player_name}%",))
    results = cursor.fetchall()
    conn.close()

    result_box.delete("1.0", tk.END)
    if not results:
        result_box.insert(tk.END, "No player found.")
    else:
        for row in results:
            result_box.insert(tk.END,
               f"Name: {row[0]}\n"
               f"Position: {row[1]}\n"
               f"Sub-position: {row[2]}\n"
               f"Citizenship: {row[3]}\n"
               f"Country of Birth: {row[4]}\n"
               f"City of Birth: {row[5]}\n"
               f"Current Club: {row[6]}\n"
               f"{'-'*40}\n"
            )

def show_player_clubs():
    player_name = player_entry.get().strip()
    if not player_name:
        messagebox.showwarning("Input Error", "Please enter a player name.")
        return

    query = """
        SELECT
            p.name AS player_name,
            COUNT(DISTINCT t.to_club_id) AS clubs_played_for
        FROM
            player p
        JOIN
            transfers t ON p.player_id = t.player_id
        WHERE
            p.name LIKE %s
        GROUP BY
            p.player_id, p.name;
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (f"%{player_name}%",))
        results = cursor.fetchall()
        conn.close()

        clubs_result_box.delete("1.0", tk.END)
        if results:
            for row in results:
                clubs_result_box.insert(tk.END, f"Player: {row[0]}\nClubs Played For: {row[1]}\n\n")
        else:
            clubs_result_box.insert(tk.END, "No data found for the entered player name.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def show_club_spending():
    club_name = club_spending_entry.get().strip()
    if not club_name:
        messagebox.showwarning("Input Error", "Please enter a club name.")
        return

    query = """
        SELECT
            c.name AS club_name,
            SUM(CASE WHEN t.to_club_id = c.club_id THEN t.market_value_in_eur ELSE 0 END) AS spending,
            SUM(CASE WHEN t.from_club_id = c.club_id THEN t.market_value_in_eur ELSE 0 END) AS revenue,
            SUM(CASE WHEN t.to_club_id = c.club_id THEN t.market_value_in_eur ELSE 0 END) -
            SUM(CASE WHEN t.from_club_id = c.club_id THEN t.market_value_in_eur ELSE 0 END) AS net_spending
        FROM
            club c
        LEFT JOIN
            transfers t ON c.club_id IN (t.to_club_id, t.from_club_id)
        WHERE
            c.name LIKE %s
        GROUP BY
            c.club_id, c.name;
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query, (f"%{club_name}%",))
        result = cursor.fetchone()
        conn.close()

        spending_result_box.delete("1.0", tk.END)
        if result:
            spending_result_box.insert(tk.END, f"Club: {result[0]}\n")
            spending_result_box.insert(tk.END, f"Spending: €{result[1]:,.0f}\n")
            spending_result_box.insert(tk.END, f"Revenue: €{result[2]:,.0f}\n")
            spending_result_box.insert(tk.END, f"Net Spending: €{result[3]:,.0f}\n")
        else:
            spending_result_box.insert(tk.END, "No data found for the entered club name.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred:\n{e}")

def show_valuation_trend():
    player_name = valuation_entry.get().strip()
    if not player_name:
        messagebox.showwarning("Input Error", "Please enter a player name.")
        return
    
    try:
        # Connect to database
        conn = connect_db()
        cursor = conn.cursor()
        
        # Get player_id
        cursor.execute("SELECT player_id FROM player WHERE name LIKE %s", (f"%{player_name}%",))
        player_result = cursor.fetchone()
        if not player_result:
            messagebox.showinfo("Not Found", f"No player found with name: {player_name}")
            return
        
        player_id = player_result[0]
        
        # Fetch valuation data
        query = """
            SELECT date, market_value_in_eur 
            FROM player_valuation 
            WHERE player_id = %s 
            ORDER BY date
        """
        cursor.execute(query, (player_id,))
        data = cursor.fetchall()
        
        if not data:
            messagebox.showinfo("No Data", "No market valuation data available for this player.")
            return
        
        dates = [datetime.strptime(str(row[0]), "%Y-%m-%d") for row in data]
        values = [row[1] for row in data]
        
        # Plot trend line
        plt.figure(figsize=(10, 5))
        line, = plt.plot(dates, values, marker='o', linestyle='-', color='teal')
        plt.title(f"Market Value Trend: {player_name}")
        plt.xlabel("Date")
        plt.ylabel("Market Value (EUR)")
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)
        
        # Interactive click to show value
        cursor_annotate = mplcursors.cursor(line, hover=False)
        cursor_annotate.connect("add", lambda sel: sel.annotation.set_text(f"{values[int(sel.index)]:,} EUR"))
        plt.show()
        
        cursor.close()
        conn.close()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def show_oldest_players():
    try:
        n = int(entry_top_n_oldest.get())
        if n <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a positive number for Top N.")
        return

    query = f"""
        SELECT 
            name,
            country_of_citizenship,
            date_of_birth,
            TIMESTAMPDIFF(YEAR, date_of_birth, CURDATE()) AS age
        FROM 
            player
        WHERE 
            date_of_birth IS NOT NULL
        ORDER BY 
            age DESC
        LIMIT {n};
    """

    try:
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()

        oldest_result_box.delete("1.0", tk.END)
        if not results:
            oldest_result_box.insert(tk.END, "No data found.\n")
        else:
            for row in results:
                oldest_result_box.insert(tk.END, 
                    f"Name: {row[0]}\n"
                    f"Nationality: {row[1]}\n"
                    f"Date of Birth: {row[2]}\n"
                    f"Age: {row[3]} years\n"
                    f"{'-'*40}\n"
                )

    except mysql.connector.Error as e:
        messagebox.showerror("Database Error", str(e))

# ---------- UI Setup ---------- #

root = tk.Tk()
root.title("Football Analytics Dashboard")
root.geometry("900x700")
notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

# ---------- Tab 1: Top Goal Scorers ---------- #
frame_goals = tk.Frame(notebook, bg="white")
notebook.add(frame_goals, text="Top Scorers")

tk.Label(frame_goals, text="Top N:", bg="white").grid(row=0, column=0, padx=5, pady=5)
entry_top_n_goals = tk.Entry(frame_goals)
entry_top_n_goals.grid(row=0, column=1, padx=5)

tk.Label(frame_goals, text="Filter by Club:", bg="white").grid(row=1, column=0)
club_choice = ttk.Combobox(frame_goals, values=["All"] + fetch_clubs())
club_choice.set("All")
club_choice.grid(row=1, column=1)

tk.Label(frame_goals, text="Filter by Season:", bg="white").grid(row=2, column=0)
season_choice = ttk.Combobox(frame_goals, values=["All"] + fetch_seasons())
season_choice.set("All")
season_choice.grid(row=2, column=1)

tk.Label(frame_goals, text="Filter by Nationality:", bg="white").grid(row=3, column=0)
nationality_choice = ttk.Combobox(frame_goals, values=["All"] + fetch_nationalities())
nationality_choice.set("All")
nationality_choice.grid(row=3, column=1)

tk.Button(frame_goals, text="Show Top Scorers", command=show_top_performers_by_goals).grid(row=4, column=0, columnspan=2, pady=10)

goal_result_box = tk.Text(frame_goals, width=100, height=25)
goal_result_box.grid(row=5, column=0, columnspan=4, padx=10, pady=10)

# ---------- Tab 2: Aggressive Players ---------- #
frame_aggressive = tk.Frame(notebook, bg="white")
notebook.add(frame_aggressive, text="Aggressive Players")

tk.Label(frame_aggressive, text="Top N:", bg="white").grid(row=0, column=0)
entry_top_n_aggressive = tk.Entry(frame_aggressive)
entry_top_n_aggressive.grid(row=0, column=1)

tk.Label(frame_aggressive, text="Card Type:", bg="white").grid(row=1, column=0)
card_choice = ttk.Combobox(frame_aggressive, values=["yellow_cards", "red_cards"])
card_choice.set("yellow_cards")
card_choice.grid(row=1, column=1)

tk.Button(frame_aggressive, text="Show Aggressive Players", command=show_top_aggressive_players).grid(row=2, column=0, columnspan=2, pady=10)

aggressive_result_box = tk.Text(frame_aggressive, width=100, height=25)
aggressive_result_box.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

# ---------- Tab 3: Transfer Flowchart ---------- #
frame_transfer = tk.Frame(notebook, bg="white")
notebook.add(frame_transfer, text="Transfer Flowchart")

tk.Label(frame_transfer, text="Enter Player Name:", bg="white").grid(row=0, column=0, padx=5, pady=5)
entry_player_name = tk.Entry(frame_transfer)
entry_player_name.grid(row=0, column=1, padx=5)
tk.Button(frame_transfer, text="Show Flowchart", command=show_transfer_flowchart).grid(row=0, column=2, padx=5)

# Scrollable Canvas
canvas_frame = tk.Frame(frame_transfer)
canvas_frame.grid(row=1, column=0, columnspan=3, pady=10)

flowchart_canvas = tk.Canvas(canvas_frame, width=800, height=400, bg="white")
scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=flowchart_canvas.yview)
flowchart_canvas.configure(yscrollcommand=scrollbar.set)

flowchart_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# ---------- Tab 4: Player Details Finder ---------- #
frame_player_details = tk.Frame(notebook, bg="white")
notebook.add(frame_player_details, text="Player Finder")

tk.Label(frame_player_details, text="Enter Player Name:", bg="white").grid(row=0, column=0, padx=5, pady=5)
entry_name = tk.Entry(frame_player_details)
entry_name.grid(row=0, column=1, padx=5)
tk.Button(frame_player_details, text="Search", command=search_player_details).grid(row=0, column=2, padx=5)

result_box = tk.Text(frame_player_details, width=100, height=25)
result_box.grid(row=1, column=0, columnspan=4, padx=10, pady=10)

# ---------- Tab 5: Player Club History ---------- #
frame_club_history = tk.Frame(notebook, bg="white")
notebook.add(frame_club_history, text="Club History")

tk.Label(frame_club_history, text="Enter Player Name:", font=("Helvetica", 12), bg="white").pack(pady=5)
player_entry = tk.Entry(frame_club_history, font=("Helvetica", 12), width=40)
player_entry.pack(pady=5)

tk.Button(frame_club_history, text="Show Clubs Played For", command=show_player_clubs, bg="black", fg="white", font=("Helvetica", 12)).pack(pady=10)

clubs_result_box = tk.Text(frame_club_history, height=15, width=80, bg="white", fg="black", font=("Courier", 10))
clubs_result_box.pack(padx=10, pady=10)

# ---------- Tab 6: Club Transfer Spending ---------- #
frame_club_spending = tk.Frame(notebook, bg="white")
notebook.add(frame_club_spending, text="Club Spending")

tk.Label(frame_club_spending, text="Enter Club Name:", font=("Helvetica", 12), bg="white").pack(pady=5)
club_spending_entry = tk.Entry(frame_club_spending, font=("Helvetica", 12), width=40)
club_spending_entry.pack(pady=5)

tk.Button(frame_club_spending, text="Show Spending Info", command=show_club_spending, bg="black", fg="white", font=("Helvetica", 12)).pack(pady=10)

spending_result_box = tk.Text(frame_club_spending, height=15, width=80, bg="white", fg="black", font=("Courier", 10))
spending_result_box.pack(padx=10, pady=10)

# ---------- Tab 7: Player Valuation Trend ---------- #
frame_valuation = tk.Frame(notebook, bg="white")
notebook.add(frame_valuation, text="Valuation Trend")

tk.Label(frame_valuation, text="Enter Player Name:", font=("Helvetica", 12), bg="white").pack(pady=10)
valuation_entry = tk.Entry(frame_valuation, font=("Helvetica", 12), width=40)
valuation_entry.pack(pady=5)

tk.Button(frame_valuation, text="Show Valuation Trend", command=show_valuation_trend, 
          bg="black", fg="white", font=("Helvetica", 12)).pack(pady=20)

# ---------- Tab 8: Oldest Players ---------- #
frame_oldest = tk.Frame(notebook, bg="white")
notebook.add(frame_oldest, text="Oldest Players")

tk.Label(frame_oldest, text="Top N Oldest Players:", font=("Helvetica", 12), bg="white").pack(pady=10)
entry_top_n_oldest = tk.Entry(frame_oldest, font=("Helvetica", 12), width=10)
entry_top_n_oldest.pack(pady=5)

tk.Button(frame_oldest, text="Show Oldest Players", command=show_oldest_players, 
          bg="black", fg="white", font=("Helvetica", 12)).pack(pady=10)

oldest_result_box = tk.Text(frame_oldest, height=20, width=80, bg="white", fg="black", font=("Courier", 10))
oldest_result_box.pack(padx=10, pady=10)

root.mainloop()