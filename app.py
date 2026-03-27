import json
import tkinter as tk
from tkinter import ttk, messagebox
from collections import defaultdict
import pandas as pd

class NestedDropdownParser:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.data = self.load_json()
        self.filtered_variables = self.filter_variables()
        self.hierarchy = self.build_hierarchy()
        self.root = None
        self.dropdowns = []
        self.selected_path = []
        self.result_var = None
        self.variable_list = []
        
    def load_json(self):
        """Load and parse the JSON file"""
        try:
            with open(self.json_file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file '{self.json_file_path}' not found")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in '{self.json_file_path}'")
    
    def filter_variables(self):
        """Filter variables where group is not 'N/A'"""
        filtered = {}
        for var_name, var_data in self.data.get('variables', {}).items():
            if var_data.get('group') != 'N/A':
                filtered[var_name] = var_data
        return filtered
    
    def build_hierarchy(self):
        """Build hierarchical structure with concept as first level, then labels"""
        hierarchy = defaultdict(lambda: defaultdict(set))
        
        for var_name, var_data in self.filtered_variables.items():
            concept = var_data.get('concept', '')
            label = var_data.get('label', '')
            label_parts = label.split('!!')
            
            # Build path: concept + label parts
            full_path = [concept] + label_parts
            
            # Build nested structure
            current_path = []
            for i, part in enumerate(full_path):
                current_path.append(part)
                path_key = '::'.join(current_path)
                
                # Store variable info at every level (not just leaf nodes)
                hierarchy[path_key]['_variables'].add((var_name, label, concept))
                
                if i == 0:
                    # First level (concept)
                    hierarchy['_root']['_children'].add(part)
                else:
                    # Add as child of parent
                    parent_path = '::'.join(current_path[:-1])
                    hierarchy[parent_path]['_children'].add(part)
        
        return hierarchy
    
    def get_options_for_level(self, level, selected_path):
        """Get available options for a specific level given the selected path"""
        if level == 0:
            return sorted(list(self.hierarchy['_root']['_children']))
        
        current_path = '::'.join(selected_path[:level])
        return sorted(list(self.hierarchy[current_path]['_children']))
    
    def get_final_variables(self, selected_path):
        """Get variables for the complete selected path"""
        path_key = '::'.join(selected_path)
        return list(self.hierarchy[path_key]['_variables'])
    
    def has_children(self, selected_path):
        """Check if the current path has children"""
        path_key = '::'.join(selected_path)
        return len(self.hierarchy[path_key]['_children']) > 0
    
    def create_gui(self):
        """Create the GUI with dynamic dropdown menus"""
        self.root = tk.Tk()
        self.root.title("Nested Variable Selector")
        self.root.geometry("1600x600")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Select Variable", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Dropdown frame
        self.dropdown_frame = ttk.Frame(main_frame)
        self.dropdown_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Button frame
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Select current level button (initially hidden)
        self.select_button = ttk.Button(self.button_frame, text="Select Current Level", 
                                       command=self.select_current_level)
        self.select_button.grid(row=0, column=0, padx=5)
        self.select_button.grid_remove()  # Hide initially
        
        # Status label
        self.status_label = ttk.Label(self.button_frame, text="", foreground="blue")
        self.status_label.grid(row=0, column=1, padx=10)

        # Save button
        self.save_button = ttk.Button(self.button_frame, text= 'Save selected variables', command=self.save_selected_variables)
        self.save_button.grid(row=1,column=0,padx=5)
        
        # Result display
        result_frame = ttk.LabelFrame(main_frame, text="Selected Variable", padding="10")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.result_var = tk.StringVar()
        result_text = tk.Text(result_frame, height=8, width=70, wrap=tk.WORD)
        result_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Scrollbar for result text
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=result_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        result_text.config(yscrollcommand=scrollbar.set)
        
        self.result_text = result_text
        
        # Initialize first dropdown
        self.create_dropdown(0)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        
    def create_dropdown(self, level):
        """Create a dropdown for the specified level"""
        # Clear dropdowns from this level onwards
        for i in range(level, len(self.dropdowns)):
            if i < len(self.dropdowns):
                self.dropdowns[i]['frame'].destroy()
        
        self.dropdowns = self.dropdowns[:level]
        self.selected_path = self.selected_path[:level]
        
        # Get options for this level
        try:
            options = self.get_options_for_level(level, self.selected_path)
        except:
            return
        
        if not options:
            return
        
        # Create frame for this dropdown
        dropdown_frame = ttk.Frame(self.dropdown_frame)
        dropdown_frame.grid(row=level, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Create label
        level_name = "Concept" if level == 0 else f"Level {level}"
        label = ttk.Label(dropdown_frame, text=f"{level_name}:")
        label.grid(row=0, column=0, padx=(0, 10))
        
        # Create dropdown
        var = tk.StringVar()
        dropdown = ttk.Combobox(dropdown_frame, textvariable=var, values=options, 
                               state="readonly", width=200)
        dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Store dropdown info
        dropdown_info = {
            'frame': dropdown_frame,
            'var': var,
            'dropdown': dropdown,
            'level': level
        }
        self.dropdowns.append(dropdown_info)
        
        # Bind selection event
        dropdown.bind('<<ComboboxSelected>>', lambda e: self.on_selection_change(level))
        
        # Configure grid
        dropdown_frame.columnconfigure(1, weight=1)
        
        # Update button visibility and status
        self.update_button_status()
    
    def update_button_status(self):
        """Update the status of the select button and status label"""
        if not self.selected_path:
            self.select_button.grid_remove()
            self.status_label.config(text="")
            return
        
        # Check if current selection has variables
        variables = self.get_final_variables(self.selected_path)
        has_variables = len(variables) > 0
        has_children = self.has_children(self.selected_path)
        
        if has_variables:
            self.select_button.grid()
            if has_children:
                self.status_label.config(text=f"({len(variables)} variable(s) available at this level, or continue selecting)")
            else:
                self.status_label.config(text=f"({len(variables)} variable(s) available)")
        else:
            self.select_button.grid_remove()
            if has_children:
                self.status_label.config(text="Please continue selecting from the next level")
            else:
                self.status_label.config(text="No variables available at this level")
    
    def select_current_level(self):
        """Select variables at the current level without going deeper"""
        self.show_results()

    def save_selected_variables(self):
        ds=pd.Series(self.variable_list)
        ds.to_csv('out.csv')
    
    def on_selection_change(self, level):
        """Handle selection change in dropdown"""
        # Update selected path
        selected_value = self.dropdowns[level]['var'].get()
        
        # Update selected_path to include this selection
        if level >= len(self.selected_path):
            self.selected_path.append(selected_value)
        else:
            self.selected_path[level] = selected_value
            self.selected_path = self.selected_path[:level + 1]
        
        # Check if this path has children
        if self.has_children(self.selected_path):
            # Create next level dropdown
            self.create_dropdown(level + 1)
        
        # Always update button status after selection
        self.update_button_status()
    
    def show_results(self):
        """Display the final results"""
        variables = self.get_final_variables(self.selected_path)
        
        if not variables:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "No variables found for this selection.")
            return
        
        # Clear previous results
        self.result_text.delete(1.0, tk.END)
        
        # Show the selected path
        path_display = " → ".join(self.selected_path)
        self.result_text.insert(tk.END, f"Selected Path: {path_display}\n")
        self.result_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Display each variable
        for i, (var_name, label, concept) in enumerate(variables):
            result_text = f"Variable {i+1}:\n"
            result_text += f"Variable Name: {var_name}\n"
            result_text += f"Label: {label}\n"
            result_text += f"Concept: {concept}\n"
            result_text += "-" * 50 + "\n\n"

            self.variable_list.append(var_name)
            
            self.result_text.insert(tk.END, result_text)
    
    def run(self):
        """Run the GUI application"""
        self.create_gui()
        self.root.mainloop()

# Example usage
if __name__ == "__main__":
    try:
        parser = NestedDropdownParser("S_variables.json")
        parser.run()
    except Exception as e:
        print(f"Error: {e}")
        
        # Create a simple error dialog if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()  # Hide main window
            messagebox.showerror("Error", str(e))
        except:
            pass