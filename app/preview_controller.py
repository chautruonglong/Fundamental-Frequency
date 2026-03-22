"""Controller for the floating waveform preview panel."""


class PreviewController:
    """Manage hover state, panel visibility, drag logic, and preview rendering."""

    def __init__(self, config, state, window, pitch_service):
        """Store dependencies needed by the hover preview flow."""

        self.config = config
        self.state = state
        self.window = window
        self.pitch_service = pitch_service

    def hide(self, event=None):
        """Hide and fully reset the floating preview panel."""

        hover = self.state.hover
        hover.pending_frame = None
        if hover.render_job is not None:
            self.window.root.after_cancel(hover.render_job)
            hover.render_job = None
        self.window.preview.destroy()
        hover.is_visible = False

    def on_canvas_motion(self, event):
        """Track waveform hover movement and schedule preview updates."""

        self._update_from_xdata(self.window.waveform_xdata_from_event(event))

    def refresh_from_pointer(self):
        """Keep the preview synchronized with the live pointer position."""

        self._update_from_xdata(self.window.waveform_xdata_from_pointer())

    def _update_from_xdata(self, xdata):
        """Update preview state from a waveform-axis x position."""

        analysis = self.state.analysis
        audio = self.state.audio
        if analysis.window_samples == 0 or audio.duration == 0:
            return

        if xdata is None or xdata < 0 or xdata > audio.duration:
            self.hide()
            return

        self._show()
        center_frame = int(xdata * len(audio.data) / audio.duration)
        frame = center_frame - analysis.window_samples // 2
        frame = max(0, min(frame, len(audio.data) - analysis.window_samples))
        self.state.hover.pending_frame = frame
        self._schedule_render()

    def keep_position_synced(self):
        """Reposition the panel on resize only when the user did not drag it."""

        if self.state.hover.is_visible and self.state.hover.has_custom_position is False:
            self._place_default()

    def hide_if_pointer_left_chart(self):
        """Hide the panel whenever the real pointer is no longer above the waveform plot."""

        if self.state.hover.is_visible and self.window.pointer_inside_wave_graph() is False:
            self.hide()

    def start_drag(self, event):
        """Remember the drag origin for the panel header."""

        self.state.hover.drag_offset_x = event.x
        self.state.hover.drag_offset_y = event.y
        self.state.hover.has_custom_position = True

    def drag_panel(self, event):
        """Move the floating preview panel with the pointer."""

        panel = self.window.preview.panel
        if panel is None:
            return

        panel_width = panel.winfo_width()
        panel_height = panel.winfo_height()
        x = panel.winfo_x() + event.x - self.state.hover.drag_offset_x
        y = panel.winfo_y() + event.y - self.state.hover.drag_offset_y
        x = max(self.config.theme.sidebar_width, min(x, self.window.root.winfo_width() - panel_width))
        y = max(0, min(y, self.window.root.winfo_height() - panel_height))
        self.window.preview.place(x, y, panel_width, panel_height)

    def _show(self):
        """Create and display the preview panel if needed."""

        self.window.preview.ensure_exists(self.start_drag, self.drag_panel)
        if self.state.hover.is_visible is False:
            if self.state.hover.has_custom_position is False:
                self._place_default()
            else:
                panel = self.window.preview.panel
                self.window.preview.place(panel.winfo_x(), panel.winfo_y(), panel.winfo_width(), panel.winfo_height())
            self.state.hover.is_visible = True
        self.window.preview.lift()

    def _place_default(self):
        """Place the panel at the standard top-centered position."""

        width, height, x, y = self.window.default_preview_position()
        self.window.preview.place(x, y, width, height)

    def _schedule_render(self):
        """Defer preview redraw work out of the raw hover callback."""

        if self.state.hover.render_job is None:
            self.state.hover.render_job = self.window.root.after_idle(self._render_pending)

    def _render_pending(self):
        """Render the most recent requested preview frame."""

        hover = self.state.hover
        hover.render_job = None
        if hover.pending_frame is None or hover.is_visible is False:
            return

        preview = self.pitch_service.build_preview_data(
            self.state.audio.data,
            self.state.audio.duration,
            self.state.analysis,
            hover.pending_frame,
        )

        figure = self.window.preview.figure
        figure.clear()
        wave_axis = figure.add_subplot(211)
        autocorr_axis = figure.add_subplot(212)
        wave_axis.set_title(self.config.text.preview_window_title_template.format(time=preview.hover_time))
        wave_axis.set_xlabel(self.config.text.preview_sample_label)
        wave_axis.set_ylabel(self.config.text.graph_amplitude_label)
        autocorr_axis.set_xlabel(self.config.text.preview_delay_label)
        autocorr_axis.set_ylabel(self.config.text.preview_autocorr_label)

        wave_axis.set_xlim(-20, self.state.analysis.window_samples)
        wave_axis.set_ylim(preview.windowed_samples.min(), preview.windowed_samples.max())
        wave_axis.plot(preview.windowed_samples, color="blue")

        autocorr_axis.set_xlim(-20, self.state.analysis.window_samples)
        autocorr_axis.set_ylim(preview.autocorrelation.min(), preview.autocorrelation.max())
        autocorr_axis.set_title(preview.title)
        autocorr_axis.plot(preview.autocorrelation, color="blue")
        autocorr_axis.hlines(
            preview.threshold,
            -20,
            self.state.analysis.window_samples,
            color="orange",
            linestyles="--",
        )
        autocorr_axis.vlines(preview.min_frame, preview.autocorrelation.min(), preview.autocorrelation.max(), color="green")
        autocorr_axis.vlines(preview.max_frame, preview.autocorrelation.min(), preview.autocorrelation.max(), color="green")
        if preview.is_periodic and preview.peak_index is not None and preview.peak_value is not None:
            autocorr_axis.scatter(preview.peak_index, preview.peak_value, color="red")

        self.window.preview.draw()
