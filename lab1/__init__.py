from random import random
from tkinter import Tk, Frame, Button, BOTH, OptionMenu, StringVar, Text, END, PhotoImage, Canvas, ALL
from lab1.liuvacuum import LIUVacuumEnvironment, ENV_CLEAN, ENV_DIRTY, ENV_WALL
from lab1.myvacuumagent import MyVacuumAgent
from lab1.randomvacuumagent import RandomVacuumAgent
from lab1.reactivevacuumagent import ReactiveVacuumAgent

DIRT_BIAS = 0.5
WALL_BIAS = 0.0

# Pre-selected PRF seeds
FIXED_SEED_1 = 1337
FIXED_SEED_2 = 69420


WORLD_COLOR_WALL = "black"
WORLD_COLOR_CLEAN = "white"
WORLD_COLOR_DIRTY = "gray"
WORLD_COLOR_HOME = "blue"

AGENT_MYVACUUMAGENT = 1
AGENT_RANDOM = 2
AGENT_REACTIVE = 3

USE_CANVAS = 1
CANVAS_BLOCK_SIZE = 30
CANVAS_BLOCK_OFFSET = 3

class Lab1:
    """
    LIUVacuumEnvironment GUI. Handles all GUI functionality and sim
    """

    def __init__(self):
        self.root = Tk()
        self.root.title("LIU Vacuum Environment")
        self.root.minsize(1024,768)
        self.root.resizable(width=False, height=False)

        self.agent_btn_dims = 22

        self.agent_img = dict()
        self.agent_img[(1, 0)] = PhotoImage(file="images/agent_east.png")
        self.agent_img[(0, 1)] = PhotoImage(file="images/agent_south.png")
        self.agent_img[(-1, 0)] = PhotoImage(file="images/agent_west.png")
        self.agent_img[(0, -1)] = PhotoImage(file="images/agent_north.png")

        self.blank_img = PhotoImage(file="images/blank.png")

        # The outermost frame within which everything is contained
        self.host_frame = Frame(self.root)

        # Log window
        self.log = Text(self.host_frame, width=50, borderwidth=2)
        self.log.pack(side="right", expand=True, fill="y")
        self.log.configure(state="disabled")

        self.options_frame = Frame(self.host_frame)

        self.vacuum_env: LIUVacuumEnvironment = None
        self.grid_frame: Frame = None
        self.grid: list = None
        self.previous_dims: list = None
        self.is_running = False


        ### Option drop-down menus

        # Environment size option menu
        self.grid_dims_getter = self.create_selection_menu(
            self.update_all,

            # Menu options: Generates tuples of the shape ("AxB", (A, B)) from a provided tuple (A, B)
            *[(str(size[1]) + "x" + str(size[0]), size) for size in
              [(5, 5), (10, 10), (15, 15), (20, 20), (5, 10), (10, 5)]]
        )

        # Environment wall bias
        self.wall_bias_getter = self.create_selection_menu(
            self.update_all,

            # Menu options: Generates tuples of the shape ("foo", foo) from a provided value foo
            *[(str(bias), bias) for bias in [0.0, 0.1, 0.2, 0.5]]
        )

        # Environment dirt bias
        self.dirt_bias_getter = self.create_selection_menu(
            self.update_all,

            # Menu options: See environment wall bias menu options
            *[(str(bias), bias) for bias in [0.1, 0.2, 0.5]]
        )

        # Environment PRF seed
        self.seed_getter = self.create_selection_menu(
            self.update_all,

            # Menu options
            ("Random", None),
            ("Seed 1", FIXED_SEED_1),
            ("Seed 2", FIXED_SEED_2),

            always_trigger_onselect=True
        )

        self.agent_getter = self.create_selection_menu(
            self.update_all,

            # Menu options
            ("MyVacuumAgent", AGENT_MYVACUUMAGENT),
            ("RandomAgent", AGENT_RANDOM),
            ("ReactiveAgent", AGENT_REACTIVE),

            always_trigger_onselect=True
        )

        # Continuous step delay
        self.delay_getter = self.create_selection_menu(
            None,

            # Menu options: See environment dirt bias menu options
            *[(str(time) + "ms", time) for time in [100, 500, 10, 50, 1000]]
        )

        def make_button(text, callback):
            """
            Shorthand for creating buttons along the top of the window

            :param text: Text to display in button
            :param callback: Button press callback
            :return: None
            """
            button = Button(self.options_frame, text=text)
            button.pack(side="left")
            button.config(command=callback)

        # Create buttons along top of window
        make_button("Prepare", self.update_all)
        make_button("Run", self.start)
        make_button("Stop", self.stop)
        make_button("Step", self.step)
        make_button("Clear Log", self.log_clear)

        # Finalize creation of holding frames
        self.options_frame.pack(side="top")
        self.host_frame.pack(expand=True, fill=BOTH)

        self.marked_agent_pos = (0, 0)
        self.marked_agent_rot = (1, 0)
        self.agent = None

        # Now that everything is properly initialized, do a full initialization of the state and graphics
        self.update_all(force=True)

    def start_main_loop(self):
        """
        Start main graphics loop.

        :return: None
        """

        self.root.mainloop()

    def append_log(self, text, end="\r\n"):
        """
        Append text to log window.

        :param text: Text to append
        :param end: Line ending to append after text
        :return: None
        """

        self.log.configure(state="normal")
        self.log.insert("end", str(text)+end)
        self.log.see(END)
        self.log.configure(state="disabled")


    def log_clear(self):
        """
        Clear log window of all text.

        :return: None
        """

        self.log.configure(state="normal")
        self.log.replace("0.0", END, "")
        self.log.configure(state="disabled")

    def refresh_tile(self, x, y):
        """
        Change color of a drawn tile to match environment model.

        :param x: X-coordinate of tile
        :param y: Y-coordinate of tile
        :return: None
        """

        # Get current state of tile in environment
        state = self.vacuum_env.world[x][y]
        new_state =  WORLD_COLOR_CLEAN  if state == ENV_CLEAN\
                else WORLD_COLOR_DIRTY  if state == ENV_DIRTY\
                else WORLD_COLOR_WALL

        if USE_CANVAS == 1:
            if new_state != self.grid_frame.itemcget(self.grid[x][y], "fill"):
                self.grid_frame.itemconfig(self.grid[x][y], fill=new_state)
        else:
            # Apply color to tile (if necessary)
            if new_state != self.grid[x][y].cget("bg"):
                self.grid[x][y].configure(bg=new_state)

    def refresh(self):
        """
        Change color of all drawn tiles to match environment model.

        :return: None
        """
        for x in range(self.vacuum_env.env_x):
            for y in range(self.vacuum_env.env_y):
                self.refresh_tile(x, y)

        if self.agent.location != self.marked_agent_pos or self.agent.facing != self.marked_agent_rot:
            self.draw_agent()

    def step(self):
        """
        Run one step in environment simulation.
        This automatically refreshes tiles.

        :return: None
        """
        self.vacuum_env.step()
        self.refresh()

    def start(self):
        """
        Start running env. steps.

        :return: None
        """
        if self.is_running:
            self.append_log("Already running")
            return

        self.append_log("Starting...")

        def run():
            """
            Continuously run steps in environment with a fixed delay between steps.
            Runs until stopped.

            :return: None
            """
            nonlocal self

            if self.is_running:
                self.step()
                self.root.after(self.delay_getter(), run)  # Trigger a timer for next call

        self.is_running = True
        run()

    def stop(self):
        """
        Stop running env. steps.

        :return: None
        """
        if self.is_running:
            self.append_log("Stopped")

        self.is_running = False

    def make_env_frame_canvas(self):
        """
        Create the grid layout representing the state of the vacuum environment using Canvas

        :return: None
        """

        width, height = self.grid_dims_getter()
        previous_width, previous_height = (self.previous_dims or (-1, -1))

        # Create an unpopulated button ref grid (filled with None for debug purposes)
        grid = [[None for _ in range(height)] for _ in range(width)]

        if self.grid_frame is None:
            self.grid_frame = Canvas(self.host_frame, width=(CANVAS_BLOCK_SIZE+CANVAS_BLOCK_OFFSET)*width, height=(CANVAS_BLOCK_SIZE+CANVAS_BLOCK_OFFSET)*height)
        else:
            self.grid_frame.delete(ALL)
            self.grid_frame.configure(width=(CANVAS_BLOCK_SIZE+CANVAS_BLOCK_OFFSET)*width, height=(CANVAS_BLOCK_SIZE+CANVAS_BLOCK_OFFSET)*height)

        #frame.create_rectangle(0,0,(block_size)*width+offset,(block_size)*height+offset, fill="red")
        for x in range(0, width):
            for y in range(0, height):
                if self.vacuum_env.world[x][y] == ENV_DIRTY:
                    color = WORLD_COLOR_DIRTY
                elif self.vacuum_env.world[x][y] == ENV_WALL:
                    color = WORLD_COLOR_WALL
                else:
                    color = WORLD_COLOR_CLEAN

                x1 = x * CANVAS_BLOCK_SIZE + CANVAS_BLOCK_OFFSET
                y1 = y * CANVAS_BLOCK_SIZE + CANVAS_BLOCK_OFFSET

                x2 = (x + 1) * CANVAS_BLOCK_SIZE
                y2 = (y + 1) * CANVAS_BLOCK_SIZE

                grid[x][y] = self.grid_frame.create_rectangle(x1,y1,x2,y2,fill=color)
        self.grid_frame.pack()
        self.grid_frame.update()
        self.grid = grid
        self.draw_agent()

    def make_env_frame(self):
        """
        Create the grid layout representing the state of the vacuum environment

        :return: None
        """

        width, height = self.grid_dims_getter()
        previous_width, previous_height = (self.previous_dims or (-1, -1))

        if (width != previous_width or height != previous_height) and self.grid:
            self.grid[self.marked_agent_pos[0]][self.marked_agent_pos[1]].configure(image=self.blank_img)

        padx = 5 if width > 15 else 8
        pady = 2 if height > 15 else 4

        def make_callback(x, y):
            """
            Create a callback function for the given coordinate

            :param x: X-coordinate
            :param y: Y-coordinate
            :return: Callback function for the given coordinate
            """
            return lambda: self.grid_click_callback(x, y)

        def make_button(x, y, container_frame):
            """
            Shorthand for creating a button in the tile grid

            :param x: X-coordinate of button
            :param y: Y-coordinate of button
            :param container_frame: Frame to hold button
            :return: Reference to button
            """
            nonlocal padx
            nonlocal pady

            btn = Button(container_frame, text="", height=self.agent_btn_dims, width=self.agent_btn_dims, padx=padx, pady=pady, image=self.blank_img)
            btn.pack(side="right")
            btn.config(command=make_callback(x, y))
            return btn

        # Create an unpopulated button ref grid (filled with None for debug purposes)
        grid = [[None for _ in range(height)] for _ in range(width)]

        frame_pad = 0 if height > 30 else 8 * (30 - height)
        if self.grid is None:
            frame = Frame(self.host_frame, pady=frame_pad, padx=0)

            for y in range(height - 1, -1, -1):
                row_frame = Frame(frame)
                for x in range(width - 1, -1, -1):
                    grid[x][y] = make_button(x, y, row_frame)
                row_frame.pack(side="bottom")

            frame.pack(side="bottom")

            self.grid_frame = frame
        else:
            # Optimization to hopefully be a bit nicer on GC (if nothing else)
            for y in range(height - 1, -1, -1):
                rel_y = height - 1 - y
                row_frame = Frame(self.grid_frame) if rel_y >= previous_height else self.grid[0][
                    previous_height - 1 - rel_y].master
                for x in range(width - 1, -1, -1):
                    rel_x = width - 1 - x
                    grid[x][y] = self.grid[previous_width - 1 - rel_x][
                        previous_height - 1 - rel_y] if rel_x < previous_width and rel_y < previous_height else make_button(
                        x, y, row_frame)

                    if rel_x < previous_width and rel_y < previous_height:
                        grid[x][y].configure(padx=padx, pady=pady)
                        grid[x][y].config(command=make_callback(x, y))

                row_frame.pack(side="bottom")

            for y in range(previous_height):
                if previous_height - y > height:
                    self.grid[0][y].master.pack_forget()
                    continue

                for x in range(previous_width):
                    if previous_width - x > width:
                        self.grid[x][y].pack_forget()

            self.grid_frame.configure(pady=frame_pad, width=frame_pad)
            self.grid_frame.pack(side="bottom")

        # Update grid
        self.grid = grid
        self.previous_dims = (width, height)

        self.draw_agent()

    def draw_agent(self):
        if USE_CANVAS == 1:
            agent_x = self.agent.location[0] * CANVAS_BLOCK_SIZE + CANVAS_BLOCK_OFFSET + CANVAS_BLOCK_SIZE / 2
            agent_y = self.agent.location[1] * CANVAS_BLOCK_SIZE + CANVAS_BLOCK_OFFSET + CANVAS_BLOCK_SIZE / 2
            agent_obj = self.grid_frame.find_withtag("agent")
            if not agent_obj:
                self.grid_frame.create_image(agent_x, agent_y, image=self.agent_img[self.agent.facing], tags="agent")
            else:
                self.grid_frame.itemconfig(agent_obj, image=self.agent_img[self.agent.facing])
                self.grid_frame.coords(agent_obj, (agent_x, agent_y))
        else:
            self.grid[self.marked_agent_pos[0]][self.marked_agent_pos[1]].configure(image=self.blank_img)
            self.grid[self.agent.location[0]][self.agent.location[1]].configure(image=self.agent_img[self.agent.facing])

        self.marked_agent_pos = self.agent.location
        self.marked_agent_rot = self.agent.facing

    def update_all(self, force=False):
        """
        Trigger a full refresh. This recreates the environment, agent and grid, as well as updates tile colours.

        :param force: Force update.
        :return: None
        """
        # Race condition: print("Selected agent:{}".format(self.agent_getter()))
        if self.vacuum_env is not None or force:
            # Ensure we stop the agent
            if self.is_running:
                self.stop()

            self.create_sim()
            if USE_CANVAS == 1:
                self.make_env_frame_canvas()
            else:
                self.make_env_frame()
            self.refresh()

    def grid_click_callback(self, x, y):
        """
        Callback to manually mark a tile as clean, dirty or a wall. Outer walls cannot be changed.
        Tile at coordinate (1, 1) cannot be a wall; only clean or dirty since this is where agents are spawned.

        :param x: X-coordinate of tile
        :param y: Y-coordinate of tile
        :return: None
        """
        w, h = self.grid_dims_getter()
        current = self.vacuum_env.world[x][y]
        if x != 0 and x != w - 1 and y != 0 and y != h - 1:
            self.vacuum_env.world[x][y] = ENV_DIRTY if current == ENV_WALL or (
                    x == 1 and y == 1 and current == ENV_CLEAN) else ENV_CLEAN if current == ENV_DIRTY else ENV_WALL
            self.refresh_tile(x, y)

    def create_selection_menu(self, cb_on_select, *opts, always_trigger_onselect=False, no_destructure=False, pass_selection_to_callback=False):
        """
        Quick way of creating a drop-down menu with a set of options and selection callbacks.

        :param cb_on_select: Menu item selection event callback
        :param opts: Menu options. These should be a list of two-element tuples where the first item is the label and the second is the corresponding value
        :param always_trigger_onselect: Whether the selection callback should be triggered even if an already-selected item was selected
        :param no_destructure: Whether option values should be destructured into the arguments of the callback
        :param pass_selection_to_callback: Whether or not to pass the selected value to the selection callback function
        :return: Getter function for the currently selected `value` (not label)
        """

        options_dict = dict()

        selection_active = StringVar(self.root)
        selection_previous = StringVar(self.root)

        for (key, value) in opts:
            options_dict[key] = value

        menu = OptionMenu(self.options_frame, selection_active, *options_dict.keys())

        def on_select(*args):
            """
            Callback function for when a menu item is selected

            :param args: Ignored arguments. Just contains the modified variable
            :return: None
            """
            # Check if a previously un-selected item was selected (or if the event should be processed anyway)
            if selection_active.get() != selection_previous.get() or always_trigger_onselect:
                selection_previous.set(selection_active.get())

                # Call callback if one was specified
                if cb_on_select:
                    if pass_selection_to_callback:
                        # Attempt to destructure parameter as much as possible
                        # This is just a lazy way of passing sets of arguments in less LOC
                        if (not no_destructure) and dir(options_dict[selection_active.get()]).__contains__("__iter__"):
                            if type(options_dict[selection_active.get()]) is dict:
                                cb_on_select(**options_dict[selection_active.get()])
                            else:
                                cb_on_select(*(options_dict[selection_active.get()]))
                        else:
                            cb_on_select(options_dict[selection_active.get()])
                    else:
                        cb_on_select()

        # Set a callback for when variable changes value
        selection_active.trace("w", on_select)

        # Pack menu if a side as packed, else assume packing will be done elsewhere
        menu.pack(side="left")

        # Select a menu option. This also triggers an initial callback
        selection_active.set(opts[0][0])

        # Return a getter function to the active *value* (not key)
        return lambda: options_dict[selection_active.get()]

    def create_sim(self):
        """
        Create environment and agent and add agent to environment
        """
        venv = LIUVacuumEnvironment(*self.grid_dims_getter(), self.dirt_bias_getter(), self.wall_bias_getter(), self.seed_getter())
        selected_agent = self.agent_getter()
        if selected_agent == AGENT_MYVACUUMAGENT:
            agent = MyVacuumAgent(*self.grid_dims_getter(), self.append_log)
        elif selected_agent == AGENT_RANDOM:
            agent = RandomVacuumAgent(*self.grid_dims_getter(), self.append_log)
        else:
            agent = ReactiveVacuumAgent(*self.grid_dims_getter(), self.append_log)
        venv.add_thing(agent)
        self.agent = agent
        self.vacuum_env = venv


run = lambda: Lab1().start_main_loop()
