import OSAview
from model import OSAmodel
import tkinter as tk
import Ando
import time

# controller class for the model-view-controller design pattern of the OSA program
class OSAcontroller:

    # init function to initialize all the variables
    def __init__(self):
        self.model = OSAmodel()
        self.view = OSAview.ANDO_OSA(self, tk.Tk())

        # bind the wavelength fields
        self.view.start_entry.bind("<Return>", self.start_changed)
        self.view.stop_entry.bind("<Return>", self.stop_changed)
        self.view.center_entry.bind("<Return>", self.update_center)
        self.view.span_entry.bind("<Return>", self.update_span)

        # bind the trace-buttons
        self.view.trace_A.bind("<Button-1>", lambda event: self.set_current_trace('A'))
        self.view.trace_B.bind("<Button-1>", lambda event: self.set_current_trace('B'))
        self.view.trace_C.bind("<Button-1>", lambda event: self.set_current_trace('C'))

        # scale button
        self.view.scale_button.bind("<Button-1>", lambda event: self.switch_scale())

        # averages-field
        self.view.averages_entry.bind("<Return>", self.averages_changed)

        # run change_measurement_state function when one of the three buttons are pressed, also pass the function which button was pressed
        self.view.auto_button.bind("<Button-1>", lambda event: self.change_measurement_state('auto'))
        self.view.stop_button.bind("<Button-1>", lambda event: self.change_measurement_state('stop'))
        self.view.single_button.bind("<Button-1>", lambda event: self.change_measurement_state('single'))

        # update hold and display buttons should run change_trace_state function
        self.view.update_button.bind("<Button-1>", lambda event: self.change_trace_state('update'))
        self.view.hold_button.bind("<Button-1>", lambda event: self.change_trace_state('hold'))
        self.view.display_button.bind("<Button-1>", lambda event: self.change_trace_display_state('display'))

        self.view.write_to_log("GUI initialized")
        self.connect_osa()
        self.set_init_values()
        self.update_function()
        self.view.run()
        

    def update_function(self):
        curr_meas_state = self.OSA.get_sweep_status()
        if curr_meas_state == 'STOP':
            self.model.measurement_state = 'STOP'
            self.view.stop_button.config(state=tk.DISABLED)
            self.view.single_button.config(state=tk.NORMAL)
            self.view.auto_button.config(state=tk.NORMAL)
        

        self.view.mainwindow.after(200, self.update_function)

        
    def connect_osa(self):
        print("connecting to OSA")
        self.view.write_to_log("Connecting to OSA...")
        # connect to the OSA
        self.OSA = Ando.Ando(5)
        if self.OSA.inst == None:
            self.view.write_to_log("Could not connect to GPIB address 5")
            self.model.connected = False
        else:
            self.view.write_to_log("Connected to GPIB address 5")
            self.model.connected = True
            self.view.log_label.configure(text="Status: Connected.")

    def set_init_values(self):
        # setting start trace
        curr_trace = self.OSA.get_current_trace()
        self.model.set_current_trace(curr_trace)
        if self.model.get_current_trace() == 'A':
            self.view.trace_A.config(state=tk.DISABLED)
        elif self.model.get_current_trace() == 'B':
            self.view.trace_B.config(state=tk.DISABLED)
        elif self.model.get_current_trace() == 'C':
            self.view.trace_C.config(state=tk.DISABLED)

        # updating display-values etc 
        curr_disp_status = self.OSA.get_display_status()
        self.model.set_trace_display_state(curr_disp_status)
        if curr_disp_status:
            self.view.display_button.config(state=tk.DISABLED)

        # updating write-status
        curr_write_status = self.OSA.get_write_status()
        self.model.trace_state = curr_write_status
        if curr_write_status:
            self.view.update_button.config(state=tk.DISABLED)
        elif not curr_write_status:
            self.view.hold_button.config(state=tk.DISABLED)

        # get sweep status
        sweep_status = self.OSA.get_sweep_status()
        self.model.set_measurement_state(sweep_status)
        if sweep_status == 'STOP':
            self.view.stop_button.config(state=tk.DISABLED)
        elif sweep_status == 'SINGLE':
            self.view.single_button.config(state=tk.DISABLED)
        elif sweep_status == 'AUTO':
            self.view.auto_button.config(state=tk.DISABLED)

        # start and stop initial states
        self.model.set_start(self.OSA.get_start_wl())
        self.model.set_stop(self.OSA.get_stop_wl())
        self.view.start_entry.insert(0, self.model.get_start())
        self.view.stop_entry.insert(0, self.model.get_stop())
        self.update_center_entry()
        self.update_span_entry()

        # averages
        self.model.set_averages(self.OSA.get_averages())
        self.view.averages_entry.insert(0, self.model.get_averages())

        # scale
        curr_scale = self.OSA.get_scale()
        self.model.set_scale(curr_scale)
        self.view.scale_button.configure(text=self.model.get_scale())
        
        # resolution
        curr_res = self.OSA.get_resolution()
        self.model.set_resolution(curr_res)
        # change resolution optionmenu to display the current resolution
        
        self.view.write_to_log("Start-values set.")
    
    # The user changed the start-values and thus the model needs to be updated and then the view, based on the values in the model
    def start_changed(self, event):
        self.model.set_start(self.view.start_entry.get())
        start_wl = self.OSA.set_start_wl(self.model.get_start())
        self.view.write_to_log("Start wavelength set to " + start_wl + " nm.")
        self.update_center_entry()
        self.update_span_entry()

    def update_stop_entry(self):
        self.view.stop_entry.delete(0, tk.END)
        self.view.stop_entry.insert(0, str(float(self.model.get_start()) + float(self.model.get_span())))

    def update_start_entry(self):
        self.view.start_entry.delete(0, tk.END)
        self.view.start_entry.insert(0, str(float(self.model.get_center()) - float(self.model.get_span()) / 2))

    def averages_changed(self, event):
        self.model.set_averages(self.view.averages_entry.get())
        self.OSA.set_averages(self.model.get_averages())
        self.view.write_to_log("Averages set to " + self.OSA.get_averages() + ".")

    # The user changed the stop-values and thus the model needs to be updated and then the view, based on the values in the model
    def stop_changed(self, event):
        self.model.set_stop(self.view.stop_entry.get())
        stop_wl = self.OSA.set_stop_wl(self.model.get_stop())
        self.view.write_to_log("Stop wavelength set to " + stop_wl + " nm.")
        self.update_center_entry()
        self.update_span_entry()

    def update_center_entry(self):
        self.view.center_entry.delete(0, tk.END)
        new_center = str((float(self.model.get_start()) + float(self.model.get_stop())) / 2)
        self.view.center_entry.insert(0, new_center)
        self.model.set_center(new_center)

    def update_center(self):
        self.model.set_center(self.view.center_entry.get())
        center_wl = self.OSA.set_center_wl(self.model.get_center())
        self.view.write_to_log("Center wavelength set to " + center_wl + " nm.")
        self.update_start_entry()
        self.update_stop_entry()
        self.update_span_entry()

    def update_span_entry(self):
        self.view.span_entry.delete(0, tk.END)
        new_span = str(float(self.model.get_stop()) - float(self.model.get_start()))
        self.view.span_entry.insert(0, new_span)
        self.model.set_span(new_span)

    def update_span(self):
        self.model.set_span(self.view.span_entry.get())
        span = self.OSA.set_span(self.model.get_span())
        self.view.write_to_log("Span wavelength set to " + span + " nm.")
        self.update_start_entry()
        self.update_stop_entry()
        self.update_center_entry()

    def set_current_trace(self, current_trace):
        self.model.set_current_trace(current_trace)
        curr = self.OSA.set_current_trace(self.model.get_current_trace())
        current_display_state = self.OSA.get_display_status()
        current_hold_state = self.OSA.get_write_status()

        # check which is the current button, disable that one, and enable all the others
        if curr == 'A':
            self.view.trace_A.config(state=tk.DISABLED)
            self.view.trace_B.config(state=tk.NORMAL)
            self.view.trace_C.config(state=tk.NORMAL)
        elif curr == 'B':
            self.view.trace_A.config(state=tk.NORMAL)
            self.view.trace_B.config(state=tk.DISABLED)
            self.view.trace_C.config(state=tk.NORMAL)
        elif curr == 'C':
            self.view.trace_A.config(state=tk.NORMAL)
            self.view.trace_B.config(state=tk.NORMAL)
            self.view.trace_C.config(state=tk.DISABLED)

        # check which is the current trace display state, disable that one, and enable all the others
        if current_display_state:
            self.model.set_trace_display_state(True)
            self.view.display_button.config(state=tk.DISABLED)
        else:
            self.model.set_trace_display_state(False)
            self.view.display_button.config(state=tk.NORMAL)
        if current_hold_state:
            self.model.set_trace_state('UPDATE')
            self.view.update_button.config(state=tk.DISABLED)
            self.view.hold_button.config(state=tk.NORMAL)
        else:
            self.model.set_trace_state('HOLD')
            self.view.hold_button.config(state=tk.DISABLED)
            self.view.update_button.config(state=tk.NORMAL)

        # write to log 
        self.view.write_to_log("Current trace set to " + self.model.get_current_trace() + ".")

    def switch_scale(self):
        if self.model.get_scale() == 'LOG':
            self.model.set_scale('LIN')
            self.OSA.set_scale(self.model.get_scale())
            self.view.scale_button.configure(text=self.model.get_scale())
            self.view.write_to_log("Scale set to " + self.OSA.get_scale() + ".")
        elif self.model.get_scale() == 'LIN':
            self.model.set_scale('LOG')
            self.OSA.set_scale(self.model.get_scale())
            self.view.scale_button.configure(text=self.model.get_scale())
            self.view.write_to_log("Scale set to " + self.OSA.get_scale() + ".")

    def resolution_changed(self, event):
        self.model.set_resolution(event)
        self.OSA.set_resolution(self.model.get_resolution())
        self.view.write_to_log("Resolution set to " + self.OSA.get_resolution() + ".")

    def change_measurement_state(self, button):
        # change value in the model
        if button == 'stop':
            self.model.measurement_state = 'STOP'
            self.OSA.set_sweep_status('STOP')
        elif button == 'single':
            self.model.measurement_state = 'SINGLE'
            self.OSA.set_sweep_status('SINGLE')
        elif button == 'auto':
            self.model.measurement_state = 'AUTO'
            self.OSA.set_sweep_status('AUTO')
        
        # disable the chosen measurement_state_button and enable all the others
        if self.model.measurement_state == 'STOP':
            self.view.stop_button.config(state=tk.DISABLED)
            self.view.single_button.config(state=tk.NORMAL)
            self.view.auto_button.config(state=tk.NORMAL)
        elif self.model.measurement_state == 'SINGLE':
            self.view.stop_button.config(state=tk.NORMAL)
            self.view.single_button.config(state=tk.DISABLED)
            self.view.auto_button.config(state=tk.NORMAL)
        elif self.model.measurement_state == 'AUTO':
            self.view.stop_button.config(state=tk.NORMAL)
            self.view.single_button.config(state=tk.NORMAL)
            self.view.auto_button.config(state=tk.DISABLED)

        # write to log
        self.view.write_to_log("Measurement state set to " + self.model.measurement_state + ".")

    def change_trace_state(self, button):
        # change value in the model
        if button == 'update':
            self.model.trace_state = 'UPDATE'
            self.OSA.set_write_status(True)
        elif button == 'hold':
            self.model.trace_state = 'HOLD'
            self.OSA.set_write_status(False)
        
        # disable the chosen trace_state_button and enable all the others
        if self.model.trace_state == 'UPDATE':
            self.view.update_button.config(state=tk.DISABLED)
            self.view.hold_button.config(state=tk.NORMAL)
        elif self.model.trace_state == 'HOLD':
            self.view.update_button.config(state=tk.NORMAL)
            self.view.hold_button.config(state=tk.DISABLED)

        # write to log
        self.view.write_to_log("Trace state set to " + self.model.trace_state + ".")

    def change_trace_display_state(self, button):
        self.model.trace_display_state = not self.model.trace_display_state
        state = self.OSA.set_display_status(self.model.get_trace_display_state())

        if state:
            self.view.display_button.config(state=tk.DISABLED)
            self.view.write_to_log("Trace display state set to display.")
        else:
            self.view.display_button.config(state=tk.NORMAL)
            self.view.write_to_log("Trace display state set to not display.")