from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import ListProperty, StringProperty, ObjectProperty
from kivy.clock import Clock
import json
import os
from datetime import datetime
from plyer import notification

class TimePickerPopup(Popup):
    selected_time = StringProperty('12:00 AM')
    
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        self.title = "Select Task Time"
        self.size_hint = (0.8, 0.6)
        
    def confirm_time(self):
        self.callback(self.selected_time)
        self.dismiss()

class ToDoItem(BoxLayout):
    text = StringProperty('')
    task_time = StringProperty('')
    image_path = StringProperty('')
    
    def delete_task(self):
        app = App.get_running_app()
        app.tasks = [task for task in app.tasks if not (task['text'] == self.text and task['time'] == self.task_time)]
        app.save_tasks()
        app.root.ids.rv.refresh_from_data()
    
    def trigger_alarm(self):
        notification.notify(
            title='⏰ Task Reminder',
            message=f'Time for: {self.text}',
            timeout=10
        )
        # Removed Window.flash() as it's not supported on all platforms

class ToDoList(BoxLayout):
    selected_time = StringProperty('12:00 AM')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scheduled_alarms = []
    
    def show_time_picker(self):
        def update_time(selected_time):
            self.selected_time = selected_time
            self.ids.selected_time.text = selected_time
            
        time_picker = TimePickerPopup(callback=update_time)
        time_picker.open()
    
    def add_task(self):
        task_text = self.ids.task_input.text.strip()
        selected_time = self.selected_time
        
        if task_text:
            app = App.get_running_app()
            new_task = {
                'text': task_text,
                'time': selected_time,
                'image': self.ids.image_input.text.strip()
            }
            app.tasks.append(new_task)
            self.ids.task_input.text = ""
            self.ids.image_input.text = ""
            self.ids.rv.refresh_from_data()
            app.save_tasks()
            self.schedule_alarm(new_task)
    
    def schedule_alarm(self, task):
        try:
            time_str = task['time']
            time_obj = datetime.strptime(time_str, '%I:%M %p').time()
            
            def check_alarm(dt):
                now = datetime.now().time()
                if now.hour == time_obj.hour and now.minute == time_obj.minute:
                    for child in self.ids.rv.children[0].children:
                        if hasattr(child, 'text') and child.text == task['text']:
                            child.trigger_alarm()
                            return False
            
            alarm = Clock.schedule_interval(check_alarm, 60)
            self.scheduled_alarms.append(alarm)
        except ValueError:
            print("Invalid time format")

class WholesomeToDoApp(App):
    tasks = ListProperty([])
    
    def build(self):
        self.load_tasks()
        return ToDoList()
    
    def on_stop(self):
        self.save_tasks()
    
    def load_tasks(self):
        if os.path.exists('tasks.json'):
            with open('tasks.json', 'r') as f:
                self.tasks = json.load(f)
    
    def save_tasks(self):
        with open('tasks.json', 'w') as f:
            json.dump(self.tasks, f)

if __name__ == '__main__':
    WholesomeToDoApp().run()