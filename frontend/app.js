const { createApp } = Vue

createApp({
    data() {
        return {
            currentTime: '',
            currentDate: '',
            todoWorkouts: [],
            tasks: [],
            
            selectedTask: null,
            showSubTaskModal: false,
            showArchiveModal: false,
            
            newTask: { title: '', description: '', repeat_interval: '' },
            newSubTaskName: {}, // task_id -> title
            
            showTaskModal: false,
            showRoutineModal: false,
            showAIModal: false,
            showMissedModal: false,
            showFABMenu: false,
            
            workoutsCompletedThisWeek: 0,
            yearlyWorkouts: 0,
            taskPoints: 0,
            totalWaterDays: 0,
            
            aiPrompt: '',
            isGeneratingAI: false,

            waterProgress: 0,
            waterBottleCount: 0,
            
            habits: [],
            shoppingItems: [],
            habitsTab: 'habits', // 'habits' or 'shopping'
            newShoppingName: '',
            newShoppingLevel: 1,
            showHabitsModal: false,
            newHabitTitle: '',
            todayDateStr: '',
            dayTimeProgress: 0,
            clockInterval: null,
        }
    },
    computed: {
        yearProgress() {
            const now = new Date();
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
        // Removed userXPProgress, adding workout isolation
        allTodaysWorkouts() {
            const now = new Date();
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const todayStr = `${year}-${month}-${day}`;
            
            const protocolTitle = `Daily Protocol ${todayStr}`;
            const protocol = this.tasks.find(t => t.title === protocolTitle);
            
            const todayName = now.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
            const specificWorkout = this.tasks.find(t => this.isWorkoutForDay(t, todayName));

            const workouts = [];
            
            if (protocol) {
                let p_subs = protocol.sub_tasks || [];
                let morningExercises = [];
                let powers = [];
                p_subs.forEach(st => {
                    if (st.title.toLowerCase() === 'drink power') {
                        powers.push(st);
                    } else {
                        morningExercises.push(st);
                    }
                });

                if (morningExercises.length > 0) {
                    workouts.push({
                        id: 'virtual-morning',
                        isVirtualChild: true,
                        parentProtocol: protocol,
                        title: 'Morning Workout',
                        sub_tasks: morningExercises,
                        completed: morningExercises.every(st => Number(st.completed) === 1 || st.completed === true),
                        progress: Math.round((morningExercises.filter(st => Number(st.completed) === 1 || st.completed === true).length / morningExercises.length) * 100)
                    });
                }

                if (powers[0]) {
                    workouts.push({
                        id: 'virtual-power-1',
                        isVirtualChild: true,
                        parentProtocol: protocol,
                        title: 'Drink Power',
                        sub_tasks: [powers[0]],
                        completed: Number(powers[0].completed) === 1 || powers[0].completed === true,
                        progress: (Number(powers[0].completed) === 1 || powers[0].completed === true) ? 100 : 0
                    });
                }

                if (specificWorkout) workouts.push(specificWorkout);

                if (powers[1]) {
                    workouts.push({
                        id: 'virtual-power-2',
                        isVirtualChild: true,
                        parentProtocol: protocol,
                        title: 'Drink Power',
                        sub_tasks: [powers[1]],
                        completed: Number(powers[1].completed) === 1 || powers[1].completed === true,
                        progress: (Number(powers[1].completed) === 1 || powers[1].completed === true) ? 100 : 0
                    });
                }
            } else if (specificWorkout) {
                workouts.push(specificWorkout);
            }
            
            return workouts;
        },
        // todaysWorkouts removed — use allTodaysWorkouts directly
        firstIncompleteWorkout() {
            return this.allTodaysWorkouts.find(w => Number(w.completed) !== 1 && w.completed !== true);
        },
        todaysPlanOverallProgress() {
            const workouts = this.allTodaysWorkouts;
            if (workouts.length === 0) return 0;
            const completed = workouts.filter(w => Number(w.completed) === 1 || w.completed === true).length;
            return Math.round((completed / workouts.length) * 100);
        },
        tomorrowsWorkout() {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            const tomorrowName = tomorrow.toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
            return this.tasks.find(t => this.isWorkoutForDay(t, tomorrowName));
        },
        regularTasks() {
            const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
            return this.tasks.filter(t => {
                const isWorkout = days.some(d => this.isWorkoutForDay(t, d));
                const isProtocol = t.title.toLowerCase().startsWith('daily protocol');
                return !isWorkout && !isProtocol;
            });
        },
        waterTrackClass() {
            if (this.waterBottleCount === 0) return 'w-1.5 bg-ink/5 border border-ink/10';
            if (this.waterBottleCount === 1) return 'w-3 bg-indigo/10 border border-indigo/30 shadow-[0_0_12px_rgba(79,70,229,0.3)] animate-pulse';
            if (this.waterBottleCount === 2) return 'w-5 bg-goldc/10 border border-goldc/40 shadow-[0_0_25px_rgba(229,181,0,0.4)] animate-pulse';
            return 'w-6 bg-goldc/20 shadow-[0_0_30px_rgba(229,181,0,0.6)] border border-goldc/60';
        },
        waterFillClass() {
            if (this.waterBottleCount === 0) return 'bg-blue-400';
            if (this.waterBottleCount === 1) return 'bg-indigo shadow-[0_0_20px_rgba(79,70,229,0.9)] brightness-110';
            if (this.waterBottleCount === 2) return 'bg-goldc shadow-[0_0_30px_rgba(229,181,0,1)] brightness-125';
            return 'bg-white shadow-[0_0_40px_rgba(255,255,255,1)]';
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
        this.updateClock();
        this.clockInterval = setInterval(this.updateClock, 1000);
        this.fetchTodoWorkouts();
        this.fetchTasks();
        this.fetchStats();
        this.loadWater();
        this.fetchHabits();
        this.fetchShoppingItems();
    },
    beforeUnmount() {
        if (this.clockInterval) {
            clearInterval(this.clockInterval);
            this.clockInterval = null;
        }
    },
    methods: {
        async fetchHabits() {
            this.habits = await this.apiCall('/api/habits') || [];
        },
        async addHabit() {
            if (!this.newHabitTitle.trim()) return;
            await this.apiCall('/api/habits', 'POST', { title: this.newHabitTitle });
            this.newHabitTitle = '';
            this.fetchHabits();
        },
        async deleteHabit(habitId) {
            await this.apiCall(`/api/habits/${habitId}`, 'DELETE');
            this.fetchHabits();
        },
        async fumbleHabit(habit) {
            try {
                const updated = await this.apiCall(`/api/habits/${habit.id}/fumble`, 'POST');
                // The server is the source of truth: it stores streak -1 with
                // last_completed_at = today, which auto-advances to Day 1
                // on the next day's fetch (streak 0).
                if (updated && typeof updated.streak === 'number') {
                    habit.streak = updated.streak;
                    habit.last_completed_at = updated.last_completed_at;
                }
                await this.fetchHabits();
                await this.fetchStats();
            } catch (e) {
                console.error("Fumble error:", e);
            }
        },
        async loadWater() {
            try {
                const res = await fetch('/api/water/today');
                const data = await res.json();
                const count = data.count || 0;
                this.waterBottleCount = Math.min(count, 3);
                this.waterProgress = count >= 3 ? 100 : 0;
            } catch (e) {
                this.waterBottleCount = 0;
                this.waterProgress = 0;
            }
        },
        async drinkWater() {
            if (this.waterBottleCount >= 3) return;
            
            if (this.waterProgress < 100) {
                this.waterProgress += 10;
                
                if (this.waterProgress >= 100) {
                    this.waterProgress = 100;
                    
                    try {
                        await this.apiCall('/api/water/drink', 'POST');
                        await this.fetchStats();
                    } catch (e) {}

                    setTimeout(() => {
                        this.waterBottleCount += 1;
                        if (this.waterBottleCount < 3) {
                            this.waterProgress = 0;
                        }
                    }, 500);
                }
            }
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
            this.currentTime = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });
            this.currentDate = now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' });
            
            const year = now.getFullYear();
            const month = String(now.getMonth() + 1).padStart(2, '0');
            const day = String(now.getDate()).padStart(2, '0');
            const newDateStr = `${year}-${month}-${day}`;
            
            if (this.todayDateStr && this.todayDateStr !== newDateStr) {
                // Day changed, refresh data
                this.fetchTodoWorkouts();
                this.fetchTasks();
                this.fetchStats();
                this.loadWater();
                this.fetchHabits();
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
            const lower = task.title.toLowerCase();
            return lower.includes(dayName) && (lower.includes('workout') || lower.includes('gym'));
        },

        closeAllModals() {
            this.showTaskModal = false;
            this.showRoutineModal = false;
            this.showAIModal = false;
            this.showMissedModal = false;
            this.showFABMenu = false;
            this.showSubTaskModal = false;
            this.showArchiveModal = false;
            this.showHabitsModal = false;
            this.selectedTask = null;
        },

        async completeFullWorkout(workout) {
            if (workout.sub_tasks && workout.sub_tasks.length > 0) {
                workout.sub_tasks.forEach(st => st.completed = true);
                await Promise.all(workout.sub_tasks.map(st => 
                    this.apiCall(`/api/tasks/${st.id}`, 'PUT', st)
                ));
                
                if (workout.isVirtualChild) {
                    await this.recalculateParentProgress(workout.parentProtocol);
                } else {
                    await this.recalculateParentProgress(workout);
                }
            } else {
                const wasCompleted = workout.completed;
                workout.completed = true;
                workout.progress = 100;
                await this.apiCall(`/api/tasks/${workout.id}`, 'PUT', workout);
                
                const isDailyProtocol = workout.title && workout.title.startsWith("Daily Protocol");
                const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
                const isSpecificWorkout = workout.title && this.isWorkoutForDay(workout, todayName);

                if (!wasCompleted && (isSpecificWorkout || isDailyProtocol)) {
                    this.incrementWorkoutStat();
                }
            }
            await this.fetchStats();
        },
        async fetchStats() {
            const res = await this.apiCall('/api/stats');
            if (res) {
                this.workoutsCompletedThisWeek = res.weekly_workouts;
                this.yearlyWorkouts = res.yearly_workouts || 0;
                this.taskPoints = res.task_points || 0;
                this.totalWaterDays = res.total_water_days || 0;
            }
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
            this.closeAllModals();
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
            
            const isDailyProtocol = parentTask.title && parentTask.title.startsWith("Daily Protocol");
            const todayName = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase();
            const isSpecificWorkout = parentTask.title && this.isWorkoutForDay(parentTask, todayName);

            if (parentTask.completed && !wasCompleted && (isSpecificWorkout || isDailyProtocol)) {
                this.incrementWorkoutStat();
            }
        },
        async deleteTask(id) {
            await this.apiCall(`/api/tasks/${id}`, 'DELETE');
            this.fetchTasks();
        },
        toggleTask(task) {
            this.selectedTask = task;
            this.showSubTaskModal = true;
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
        },

        // --- AI ---
        async generateTasksAI() {
            if (!this.aiPrompt.trim()) return;

            this.isGeneratingAI = true;
            try {
                const result = await this.apiCall('/api/generate_tasks', 'POST', {
                    prompt: this.aiPrompt
                });
                
                if (result) {
                    this.aiPrompt = '';
                    if (result.tasks && result.tasks.length > 0) {
                        await this.fetchTasks();
                    }
                    if (result.habits && result.habits.length > 0) {
                        await this.fetchHabits();
                    }
                    if (result.shopping_items && result.shopping_items.length > 0) {
                        await this.fetchShoppingItems();
                    }
                    this.closeAllModals();
                }
            } catch (err) {
                console.error("AI Generation failed", err);
            } finally {
                this.isGeneratingAI = false;
            }
        }
    }
}).mount('#app')
