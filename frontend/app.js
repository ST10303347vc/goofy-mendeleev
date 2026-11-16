const { createApp } = Vue
const clockFormat = new Intl.DateTimeFormat('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
const dateFormat = new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'short', day: 'numeric' });

createApp({
    data() {
        return {
            usesNativeTheme: Boolean(window.goofyNativeTheme),
            browserTheme: document.documentElement.dataset.theme,
            currentTime: '',
            currentDate: '',
            todoWorkouts: [],
            training: { day: null, today: [], tomorrow: null },
            trainingPending: null,
            tasks: [],
            
            selectedTask: null,
            modal: null,
            modalTrigger: null,
            
            newTask: { title: '', description: '', repeat_interval: '' },
            newSubTaskName: {}, // task_id -> title
            
            
            workoutsCompletedThisWeek: 0,
            yearlyWorkouts: 0,
            taskPoints: 0,
            totalWaterDays: 0,
            

            water: null,
            waterTapQueue: null,
            
            habits: [],
            shoppingItems: [],
            habitsTab: 'habits', // 'habits' or 'shopping'
            newShoppingName: '',
            newShoppingLevel: 1,
            newHabitTitle: '',
            newHabitKind: 'build',
            pendingHabit: null,
            reflection: '',
            reflectionSaved: false,
            reflectionLoaded: false,
            todayDateStr: '',
            dayTimeProgress: 0,
            clockInterval: null,
            dashboardPending: null,
            clockMinute: 0,
        }
    },
    computed: {
        yearProgress() {
            const now = new Date(this.clockMinute * 60_000);
            const start = new Date(now.getFullYear(), 0, 1);
            const end = new Date(now.getFullYear() + 1, 0, 1);
            const percent = ((now - start) / (end - start)) * 100;
            return percent.toFixed(1);
        },
        incompleteTasksCount() {
            return this.tasks.filter(t => !t.completed).length;
        },
        totalTaskProgress() {
            if (this.tasks.length === 0) return 0;
            const completed = this.tasks.filter(t => t.completed).length;
            return Math.round((completed / this.tasks.length) * 100);
        },
        yourProgress() {
            const p = (this.taskPoints / 1000) * 100;
            return Math.min(p, 100).toFixed(1);
        },
        fitnessProgress() {
            // Target is 189 (79 weekday gym routines + 110 daily protocols) for the rest of the year
            const p = (this.yearlyWorkouts / 189) * 100;
            return Math.min(p, 100).toFixed(1);
        },
        allTodaysWorkouts() {
            const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
            const custom = this.tasks.filter(task => this.isWorkoutForDay(task, todayName));
            return [...this.training.today, ...custom];
        },
        todaysPlanOverallProgress() {
            const required = this.allTodaysWorkouts.filter(workout => !workout.optional);
            if (!required.length) return 0;
            return Math.round(required.filter(workout => workout.completed).length / required.length * 100);
        },
        regularTasks() {
            const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            return this.tasks.filter(t => {
                const isWorkout = days.some(d => this.isWorkoutForDay(t, d));
                const isProtocol = t.title.toLowerCase().startsWith('daily protocol');
                return !isWorkout && !isProtocol;
            });
        },
        waterBottleCount() {
            return this.water?.count ?? 0;
        },
        waterAtBest() {
            return this.water?.next_tier === null;
        },
        waterProgress() {
            if (this.waterAtBest) return 100;
            return this.water ? Math.round(this.water.partial_ml / this.water.bottle_ml * 100) : 0;
        },
        waterAmount() {
            return this.formatWaterAmount(this.water?.total_ml ?? 0);
        },
        waterSummary() {
            const parts = [`${this.waterAmount} logged`];
            if (this.water?.tier) parts.push(this.water.tier);
            if (this.water?.next_tier) {
                const next = this.water.next_tier;
                parts.push(`Next tier: ${next.name} at ${this.formatWaterAmount(next.total_ml)}`);
            }
            return parts.join(' · ');
        },
        waterTrackClass() {
            if (this.waterBottleCount === 0) return 'w-1.5 bg-ink/5 border border-ink/10';
            if (this.waterBottleCount === 1) return 'w-3 bg-indigo/10 border border-indigo/30 water-indigo-glow';
            if (this.waterBottleCount === 2) return 'w-5 bg-goldc/10 border border-goldc/40 water-gold-glow';
            return 'w-6 bg-goldc/20 border border-goldc/60 water-peak-glow';
        },
        waterFillClass() {
            if (this.waterBottleCount === 0) return 'bg-water';
            if (this.waterBottleCount === 1) return 'bg-indigo water-indigo-glow';
            if (this.waterBottleCount === 2) return 'bg-goldc water-gold-glow';
            return 'bg-goldc water-peak-glow';
        },
        inProgressTasks() {
            return this.regularTasks
                .filter(t => !t.completed && (Number(t.is_priority) === 1 || t.is_priority === true))
                .sort((a, b) => b.progress - a.progress)
                .slice(0, 4);
        },
        todaysDutiesTasks() {
            const inProgressIds = new Set(this.inProgressTasks.map(t => t.id));
            return this.regularTasks.filter(t => !inProgressIds.has(t.id) && !t.completed);
        },
        archivedTasks() {
            return this.regularTasks.filter(t => t.completed);
        },
        activeShoppingItems() {
            return this.shoppingItems.filter(i => !i.completed);
        },
        archivedShoppingItems() {
            return this.shoppingItems.filter(i => i.completed);
        }
    },
    mounted() {
        window.goofyReloadTasks = async () => { await this.fetchTasks(); await this.fetchStats(); };
        this.syncClock();
        this.refreshDashboard();
        document.addEventListener('visibilitychange', this.syncClock);
        document.addEventListener('keydown', this.onEscape);
    },
    beforeUnmount() {
        clearInterval(this.clockInterval);
        document.removeEventListener('visibilitychange', this.syncClock);
        document.removeEventListener('keydown', this.onEscape);
        delete window.goofyReloadTasks;
    },
    methods: {
        setBrowserTheme(value) {
            this.browserTheme = value === 'dark' ? 'dark' : 'light';
            document.documentElement.dataset.theme = this.browserTheme;
            try { localStorage.setItem('goofy-theme', this.browserTheme); } catch {}
        },
        onEscape(event) {
            if (event.key !== 'Escape' || !this.modal || event.defaultPrevented) return;
            event.preventDefault();
            this.closeModal();
        },
        syncClock() {
            clearInterval(this.clockInterval);
            this.clockInterval = null;
            if (document.hidden) return;
            this.updateClock();
            this.clockInterval = setInterval(this.updateClock, 1000);
        },
        refreshDashboard() {
            if (this.dashboardPending) return this.dashboardPending;
            this.dashboardPending = this.apiCall('/api/dashboard').then(data => {
                this.tasks = data.tasks;
                this.todoWorkouts = data.todo_workouts;
                this.training = data.training ?? this.training;
                this.applyStats(data.stats);
                this.applyWater(data.water);
                this.habits = data.habits;
                this.shoppingItems = data.shopping_items;
            }).catch(() => {
                // apiCall already displays the original error alert.
            }).finally(() => { this.dashboardPending = null; });
            return this.dashboardPending;
        },
        async fetchHabits() {
            this.habits = await this.apiCall('/api/habits') || [];
        },
        async addHabit() {
            if (!this.newHabitTitle.trim()) return;
            await this.apiCall('/api/habits', 'POST', { title: this.newHabitTitle, kind: this.newHabitKind });
            this.newHabitTitle = '';
            this.fetchHabits();
        },
        async checkInHabit(habit) {
            if (this.pendingHabit !== null) return;
            this.pendingHabit = habit.id;
            try {
                const updated = await this.apiCall(`/api/habits/${habit.id}/check-in`, 'PUT', { checked: !habit.checked_today });
                Object.assign(habit, updated);
            } finally { this.pendingHabit = null; }
        },
        async openReview(event) {
            this.openModal('review', event);
            this.reflectionSaved = false;
            this.reflectionLoaded = false;
            const record = await this.apiCall('/api/reflection');
            this.reflection = record.note;
            this.reflectionLoaded = true;
        },
        async saveReflection() {
            if (!this.reflectionLoaded) return;
            await this.apiCall('/api/reflection', 'PUT', { note: this.reflection });
            this.reflectionSaved = true;
        },
        async deleteHabit(habitId) {
            await this.apiCall(`/api/habits/${habitId}`, 'DELETE');
            this.fetchHabits();
        },
        async logLapse(habit) {
            if (this.pendingHabit !== null) return;
            this.pendingHabit = habit.id;
            try {
                const updated = await this.apiCall(`/api/habits/${habit.id}/fumble`, 'POST');
                Object.assign(habit, updated);
                await this.fetchStats();
            } finally {
                this.pendingHabit = null;
            }
        },
        formatWaterAmount(ml) {
            return `${Number((ml / 1000).toFixed(2))} L`;
        },
        applyWater(next) {
            if (!next || (this.water && (next.date < this.water.date ||
                (next.date === this.water.date && next.total_ml < this.water.total_ml)))) return;
            this.water = next;
        },
        async drinkWater() {
            if (this.waterAtBest) return;
            const previous = this.waterTapQueue ?? Promise.resolve();
            const tap = previous.then(async () => {
                await this.dashboardPending;
                if (this.waterAtBest) return;
                const result = await this.apiCall('/api/water/tap', 'POST');
                this.applyWater(result);
                if (result.points_awarded) await this.fetchStats();
            }).catch(() => {
                // The API helper already showed the error. Leave the saved fill unchanged.
            });
            this.waterTapQueue = tap;
            await tap;
            if (this.waterTapQueue === tap) this.waterTapQueue = null;
        },
        async fetchShoppingItems() {
            this.shoppingItems = await this.apiCall('/api/shopping') || [];
        },
        async addShoppingItem() {
            if (!this.newShoppingName.trim()) return;
            const level = parseInt(this.newShoppingLevel);
            if (level < 1 || level > 10) return;
            await this.apiCall('/api/shopping', 'POST', { name: this.newShoppingName, level: level });
            this.newShoppingName = '';
            this.newShoppingLevel = 1;
            this.fetchShoppingItems();
        },
        async deleteShoppingItem(id) {
            await this.apiCall(`/api/shopping/${id}`, 'DELETE');
            this.fetchShoppingItems();
        },
        async completeShoppingItem(id) {
            await this.apiCall(`/api/shopping/${id}/complete`, 'POST');
            this.fetchShoppingItems();
            this.fetchStats(); // Update taskPoints
        },
        async restoreShoppingItem(id) {
            await this.apiCall(`/api/shopping/${id}/restore`, 'POST');
            this.fetchShoppingItems();
            this.fetchStats();
        },
        updateClock() {
            const now = new Date();
            this.currentTime = clockFormat.format(now);
            const minute = Math.floor(now.getTime() / 60_000);
            if (minute === this.clockMinute) return;
            this.clockMinute = minute;
            this.currentDate = dateFormat.format(now);
            
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const newDateStr = `${year}-${month}-${day}`;
            
            if (this.todayDateStr && this.todayDateStr !== newDateStr) {
                this.refreshDashboard();
            }
            this.todayDateStr = newDateStr;
            
            this.dayTimeProgress = ((now.getHours() * 60 + now.getMinutes()) / (24 * 60)) * 100;
        },
        async apiCall(url, method = 'GET', body = null) {
            const options = {
                method,
                headers: {
                    'Content-Type': 'application/json'
                }
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            try {
                const response = await fetch(url, options);
                if (!response.ok) {
                    const err = await response.json().catch(()=>({}));
                    throw new Error(err.error || 'Network response was not ok');
                }
                return await response.json();
            } catch (error) {
                console.error("API Error:", error);
                alert("Error: " + error.message);
                throw error;
            }
        },

        isWorkoutForDay(task, dayName) {
            const lower = (task.title || '').toLowerCase();
            return lower.includes(dayName) && (lower.includes('workout') || lower.includes('gym'));
        },

        openModal(name, event) {
            this.modalTrigger = event?.currentTarget ?? document.activeElement;
            this.modal = name;
            this.$nextTick(() => this.$refs.closeButton?.focus());
        },

        closeModal() {
            if (!this.modal) return;
            const trigger = this.modalTrigger;
            this.modal = null;
            this.modalTrigger = null;
            this.selectedTask = null;
            this.$nextTick(() => { if (!this.modal) trigger?.focus(); });
        },

        async completeFullWorkout(workout) {
            if (workout.completed || this.trainingPending !== null) return;
            this.trainingPending = workout.slot || workout.id;
            try {
                if (workout.slot) {
                    const result = await this.apiCall(`/api/training/${this.training.day}/${workout.slot}/complete`, 'PUT');
                    this.training = result.training;
                    this.applyStats(result.stats);
                    return;
                }
                if (workout.sub_tasks?.length) {
                    for (const step of workout.sub_tasks) {
                        await this.apiCall(`/api/tasks/${step.id}`, 'PUT', { completed: true });
                        step.completed = true;
                    }
                    await this.recalculateParentProgress(workout);
                } else {
                    await this.apiCall(`/api/tasks/${workout.id}`, 'PUT', { completed: true, progress: 100 });
                    workout.completed = true;
                    workout.progress = 100;
                    await this.incrementWorkoutStat();
                }
            } finally {
                this.trainingPending = null;
            }
        },
        applyStats(stats) {
            this.workoutsCompletedThisWeek = stats.weekly_workouts;
            this.yearlyWorkouts = stats.yearly_workouts || 0;
            this.taskPoints = stats.task_points || 0;
            this.totalWaterDays = stats.total_water_days || 0;
        },
        async fetchStats() {
            this.applyStats(await this.apiCall('/api/stats'));
        },

        async incrementWorkoutStat() {
            const res = await this.apiCall('/api/stats/increment_workout', 'POST');
            if (res) {
                this.workoutsCompletedThisWeek = res.weekly_workouts;
                this.yearlyWorkouts = res.yearly_workouts || 0;
            }
            // Fetch remaining stats (task_points, water_days) that this endpoint no longer returns
            await this.fetchStats();
        },

        // --- Todo Workouts ---
        async fetchTodoWorkouts() {
            this.todoWorkouts = await this.apiCall('/api/todo_workouts') || [];
        },
        async completeTodo(id) {
            await this.apiCall(`/api/todo_workouts/${id}/complete`, 'PUT');
            this.fetchTodoWorkouts();
        },

        // --- Tasks ---
        async fetchTasks() {
            this.tasks = await this.apiCall('/api/tasks') || [];
        },
        async addTask() {
            if (!this.newTask.title.trim()) return;
            const payload = { ...this.newTask };
            if (payload.repeat_interval === '') payload.repeat_interval = null;
            await this.apiCall('/api/tasks', 'POST', payload);
            this.newTask.title = '';
            this.newTask.description = '';
            this.newTask.repeat_interval = '';
            this.fetchTasks();
            if (this.modal === 'task') this.closeModal();
        },
        async updateTaskProgress(task, isCheckboxTriggered) {
            if (isCheckboxTriggered) {
                task.progress = task.completed ? 100 : 0;
                if (task.completed && task.sub_tasks.length > 0) {
                    task.sub_tasks.forEach(st => st.completed = true);
                } else if (!task.completed && task.sub_tasks.length > 0) {
                    task.sub_tasks.forEach(st => st.completed = false);
                }
            } else {
                task.completed = task.progress === 100;
            }
            
            await this.apiCall(`/api/tasks/${task.id}`, 'PUT', task);
            
            if (isCheckboxTriggered && task.sub_tasks.length > 0) {
                await Promise.all(task.sub_tasks.map(st => 
                    this.apiCall(`/api/tasks/${st.id}`, 'PUT', st)
                ));
            }
        },
        async updateSubTask(virtualTask, subTask) {
            await this.apiCall(`/api/tasks/${subTask.id}`, 'PUT', subTask);
            const realParent = this.tasks.find(t => t.id === subTask.parent_id);
            if (realParent) {
                await this.recalculateParentProgress(realParent);
            }
            await this.fetchStats();
        },
        async recalculateParentProgress(parentTask) {
            const wasCompleted = parentTask.completed;
            const total = parentTask.sub_tasks.length;
            if (total === 0) return;
            
            const completed = parentTask.sub_tasks.filter(st => st.completed).length;
            parentTask.progress = Math.round((completed / total) * 100);
            parentTask.completed = parentTask.progress === 100;
            
            await this.apiCall(`/api/tasks/${parentTask.id}`, 'PUT', parentTask);
            
            const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
            const isSpecificWorkout = parentTask.title && this.isWorkoutForDay(parentTask, todayName);

            if (parentTask.completed && !wasCompleted && isSpecificWorkout) {
                await this.incrementWorkoutStat();
            }
        },
        async deleteTask(id) {
            await this.apiCall(`/api/tasks/${id}`, 'DELETE');
            this.fetchTasks();
        },
        toggleTask(task, event) {
            this.selectedTask = task;
            this.openModal('detail', event);
        },
        async togglePriority(task) {
            task.is_priority = task.is_priority ? 0 : 1;
            await this.apiCall(`/api/tasks/${task.id}`, 'PUT', { is_priority: task.is_priority });
            this.fetchTasks();
        },

        // --- Sub Tasks ---
        async deleteSubTask(parentTask, subId) {
            await this.apiCall(`/api/tasks/${subId}`, 'DELETE');
            parentTask.sub_tasks = parentTask.sub_tasks.filter(st => st.id !== subId);
            this.recalculateParentProgress(parentTask);
        },
        async completeNextSubTask(task) {
            const nextSub = task.sub_tasks.find(s => !s.completed);
            if (nextSub) {
                nextSub.completed = true;
                await this.updateSubTask(task, nextSub);
            }
        },
        async addSubTask(parentTask) {
            const title = this.newSubTaskName[parentTask.id];
            if (!title || !title.trim()) return;
            const newSub = await this.apiCall('/api/tasks', 'POST', { title, parent_id: parentTask.id });
            parentTask.sub_tasks.push(newSub);
            this.newSubTaskName[parentTask.id] = '';
            
            this.recalculateParentProgress(parentTask);
        }
    }
}).mount('#app')
