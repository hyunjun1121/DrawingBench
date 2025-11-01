import json
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import os


class DrawingEvaluator:
    """
    Evaluates LLM-generated drawings based on mouse action sequences
    """

    def __init__(self, canvas_width=1000, canvas_height=700, config_path="UI_CONFIG.json"):
        # Load UI configuration
        self.ui_config = self._load_ui_config(config_path)

        # Canvas configuration
        self.canvas_width = self.ui_config["canvas"]["width"]
        self.canvas_height = self.ui_config["canvas"]["height"]
        self.canvas_offset_x = self.ui_config["canvas"]["offset_x"]
        self.canvas_offset_y = self.ui_config["canvas"]["offset_y"]

        # Build color positions from config
        self.color_positions = []
        for color_key, color_data in self.ui_config["colors"].items():
            self.color_positions.append((
                color_data["x"],
                color_data["y"],
                color_data["hex"]
            ))

        # Build tool positions from config
        self.tool_positions = {}
        for tool_key, tool_data in self.ui_config["tools"].items():
            self.tool_positions[tool_key] = (tool_data["x"], tool_data["y"])

        # Tolerance for position matching
        self.tolerance = self.ui_config["tolerance"]

    def _load_ui_config(self, config_path):
        """Load UI configuration from JSON file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"UI config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def evaluate(self, actions, ground_truth=None, criteria=None):
        """
        Evaluate a sequence of drawing actions

        Args:
            actions: List of action dictionaries
            ground_truth: Optional ground truth data for comparison
            criteria: Dictionary of evaluation criteria

        Returns:
            Dictionary with evaluation scores and metrics
        """
        # Input validation
        if not isinstance(actions, list):
            return {
                "total_actions": 0,
                "action_breakdown": {},
                "errors": [{
                    "type": "SYNTAX_ERROR",
                    "message": "Actions must be a list/array",
                    "index": -1
                }],
                "warnings": [],
                "metrics": {
                    "tool_changes": 0,
                    "color_changes": 0,
                    "drawing_segments": 0,
                    "canvas_coverage": 0,
                    "canvas_coverage_accurate": 0,
                    "exact_colors_used": []
                },
                "score": 0.0
            }

        results = {
            "total_actions": len(actions),
            "action_breakdown": self._count_actions(actions),
            "errors": [],
            "warnings": [],
            "metrics": {}
        }

        # Run various evaluations
        results["errors"].extend(self._check_syntax_errors(actions))
        results["errors"].extend(self._check_coordinate_errors(actions))
        results["warnings"].extend(self._check_efficiency_warnings(actions))

        # Analyze action patterns
        results["metrics"]["tool_changes"] = self._count_tool_changes(actions)
        results["metrics"]["color_changes"] = self._count_color_changes(actions)
        results["metrics"]["drawing_segments"] = self._count_drawing_segments(actions)
        results["metrics"]["canvas_coverage"] = self._estimate_canvas_coverage(actions)

        # ENHANCED: Additional accurate metrics
        results["metrics"]["canvas_coverage_accurate"] = self._estimate_canvas_coverage_accurate(actions)
        results["metrics"]["exact_colors_used"] = self._detect_exact_colors_used(actions)

        # ENHANCED: Spatial accuracy metric
        if criteria and "prompt" in criteria:
            spatial_constraints = self._extract_spatial_constraints(criteria["prompt"])
            if spatial_constraints:
                results["metrics"]["spatial_accuracy"] = self._evaluate_spatial_accuracy(actions, spatial_constraints)
                results["metrics"]["spatial_constraints"] = spatial_constraints
            else:
                results["metrics"]["spatial_accuracy"] = None
                results["metrics"]["spatial_constraints"] = {}
        else:
            results["metrics"]["spatial_accuracy"] = None
            results["metrics"]["spatial_constraints"] = {}

        # ENHANCED: Action efficiency metric
        if criteria:
            results["metrics"]["action_efficiency"] = self._calculate_action_efficiency(actions, criteria)
        else:
            results["metrics"]["action_efficiency"] = None

        # Check for required actions
        if criteria:
            results["criteria_met"] = self._check_criteria(actions, criteria)
            # Store required color count for scoring
            if "required_colors" in criteria:
                results["colors_required"] = len(criteria["required_colors"])
            # Store required coverage for proportional penalty calculation
            if "min_coverage" in criteria:
                results["min_coverage"] = criteria["min_coverage"]

        # Calculate overall score
        results["score"] = self._calculate_score(results)

        # ENHANCED: Classify errors for detailed analysis
        if criteria:
            results["error_classification"] = self._classify_errors(results, criteria)
        else:
            results["error_classification"] = {
                'spatial_errors': [],
                'tool_errors': [],
                'color_errors': [],
                'planning_errors': [],
                'syntax_errors': []
            }

        return results

    def _count_actions(self, actions):
        """Count different types of actions"""
        counts = {
            "moveTo": 0,
            "click": 0,
            "mouseDown": 0,
            "mouseUp": 0,
            "unknown": 0
        }

        for action in actions:
            action_type = action.get("action", "unknown")
            if action_type in counts:
                counts[action_type] += 1
            else:
                counts["unknown"] += 1

        return counts

    def _check_syntax_errors(self, actions):
        """Check for syntax/format errors in actions"""
        errors = []

        for i, action in enumerate(actions):
            # Check if action field exists
            if "action" not in action:
                errors.append({
                    "type": "SYNTAX_ERROR",
                    "index": i,
                    "message": "Missing 'action' field"
                })
                continue

            action_type = action["action"]

            # Check for required coordinates
            if action_type in ["moveTo"]:
                if "x" not in action or "y" not in action:
                    errors.append({
                        "type": "SYNTAX_ERROR",
                        "index": i,
                        "message": f"{action_type} requires 'x' and 'y' coordinates"
                    })

            # Check for valid action types
            valid_actions = ["moveTo", "click", "mouseDown", "mouseUp"]
            if action_type not in valid_actions:
                errors.append({
                    "type": "SYNTAX_ERROR",
                    "index": i,
                    "message": f"Unknown action type: {action_type}"
                })

        return errors

    def _check_coordinate_errors(self, actions):
        """Check for coordinate boundary errors with detailed context"""
        errors = []

        for i, action in enumerate(actions):
            if "x" in action and "y" in action:
                try:
                    x, y = float(action["x"]), float(action["y"])
                except (ValueError, TypeError):
                    # Invalid coordinate types
                    errors.append({
                        "type": "SYNTAX_ERROR",
                        "index": i,
                        "message": f"Invalid coordinate types at index {i}: x={action.get('x')}, y={action.get('y')}",
                        "action_detail": f"{action.get('action')}"
                    })
                    continue

                # Check if coordinates are within screen bounds
                if x < 0 or x > 1500 or y < 0 or y > 900:
                    error_msg = self._build_coordinate_error_context(
                        action, i, x, y, "screen_bounds", actions
                    )
                    errors.append({
                        "type": "COORDINATE_ERROR",
                        "index": i,
                        "message": error_msg,
                        "action_detail": f"{action.get('action')}(x={x}, y={y})"
                    })

                # Warn if trying to draw outside canvas (only check mouseDown, not moveTo)
                if action.get("action") == "mouseDown":
                    canvas_x = x - self.canvas_offset_x
                    canvas_y = y - self.canvas_offset_y

                    if (canvas_x < 0 or canvas_x > self.canvas_width or
                        canvas_y < 0 or canvas_y > self.canvas_height):
                        error_msg = self._build_coordinate_error_context(
                            action, i, x, y, "canvas_bounds", actions
                        )
                        errors.append({
                            "type": "COORDINATE_ERROR",
                            "index": i,
                            "message": error_msg,
                            "action_detail": f"mouseDown(x={x}, y={y})"
                        })

        return errors

    def _build_coordinate_error_context(self, action, index, x, y, error_type, actions):
        """Build detailed error context with suggestions"""
        action_type = action.get("action", "unknown")

        if error_type == "screen_bounds":
            msg = f"Action at index {index}: {action_type}(x={x}, y={y}) - Coordinates out of screen bounds.\n"

            if x < 0:
                msg += f"  Problem: x={x} is negative\n"
                msg += f"  Valid range: x must be >= 0\n"
                msg += f"  Suggestion: Use x >= 0"
            elif x > 1500:
                msg += f"  Problem: x={x} exceeds screen width\n"
                msg += f"  Valid range: x must be <= 1090 (canvas right edge)\n"
                msg += f"  Suggestion: For canvas drawing, use x <= 1090"

            if y < 0:
                msg += f"  Problem: y={y} is negative\n"
                msg += f"  Valid range: y must be >= 0\n"
                msg += f"  Suggestion: Use y >= 0"
            elif y > 900:
                msg += f"  Problem: y={y} exceeds screen height\n"
                msg += f"  Valid range: y must be <= 770 (canvas bottom edge)\n"
                msg += f"  Suggestion: For canvas drawing, use y <= 770"

        elif error_type == "canvas_bounds":
            canvas_x = x - self.canvas_offset_x
            canvas_y = y - self.canvas_offset_y

            msg = f"Action at index {index}: {action_type}(x={x}, y={y}) - Drawing outside canvas area.\n"
            msg += f"  Canvas area: x ∈ [{self.canvas_offset_x}, {self.canvas_offset_x + self.canvas_width}], "
            msg += f"y ∈ [{self.canvas_offset_y}, {self.canvas_offset_y + self.canvas_height}]\n"

            if canvas_x < 0:
                msg += f"  Problem: x={x} is left of canvas (canvas starts at x={self.canvas_offset_x})\n"
                msg += f"  Suggestion: Use x >= {self.canvas_offset_x}"
            elif canvas_x > self.canvas_width:
                msg += f"  Problem: x={x} is right of canvas (canvas ends at x={self.canvas_offset_x + self.canvas_width})\n"
                msg += f"  Suggestion: Use x <= {self.canvas_offset_x + self.canvas_width}"

            if canvas_y < 0:
                msg += f"  Problem: y={y} is above canvas (canvas starts at y={self.canvas_offset_y})\n"
                msg += f"  Suggestion: Use y >= {self.canvas_offset_y}"
            elif canvas_y > self.canvas_height:
                msg += f"  Problem: y={y} is below canvas (canvas ends at y={self.canvas_offset_y + self.canvas_height})\n"
                msg += f"  Suggestion: Use y <= {self.canvas_offset_y + self.canvas_height}"

        # Add action sequence context
        msg += self._get_action_sequence_context(index, actions)

        return msg

    def _get_action_sequence_context(self, index, actions, context_range=2):
        """Get surrounding action sequence for error context"""
        start = max(0, index - context_range)
        end = min(len(actions), index + context_range + 1)

        context = "\n  Action sequence:\n"
        for i in range(start, end):
            action = actions[i]
            action_str = f"{action.get('action')}"
            if "x" in action and "y" in action:
                action_str += f"(x={action['x']}, y={action['y']})"

            if i == index:
                context += f"    [{i}] {action_str} ← ERROR\n"
            else:
                context += f"    [{i}] {action_str}\n"

        return context

    def _check_efficiency_warnings(self, actions):
        """Check for inefficient action patterns"""
        warnings = []

        # Check for too many actions
        if len(actions) > 1000:
            warnings.append({
                "type": "EFFICIENCY_WARNING",
                "message": f"Very high action count: {len(actions)} actions"
            })

        # Check for redundant moveTo
        for i in range(len(actions) - 1):
            if (actions[i].get("action") == "moveTo" and
                actions[i + 1].get("action") == "moveTo"):
                if i + 2 < len(actions) and actions[i + 2].get("action") == "moveTo":
                    warnings.append({
                        "type": "EFFICIENCY_WARNING",
                        "message": f"Multiple consecutive moveTo actions at index {i}"
                    })
                    break

        # Check for unmatched mouseDown/mouseUp
        down_count = sum(1 for a in actions if a.get("action") == "mouseDown")
        up_count = sum(1 for a in actions if a.get("action") == "mouseUp")

        if down_count != up_count:
            warnings.append({
                "type": "LOGIC_ERROR",
                "message": f"Unmatched mouseDown ({down_count}) and mouseUp ({up_count})"
            })

        return warnings

    def _count_tool_changes(self, actions):
        """Count number of tool changes"""
        tool_clicks = 0
        # Load tool coordinates from config
        tool_coords = list(self.tool_positions.values())

        for i, action in enumerate(actions):
            if action.get("action") == "click":
                x, y = action.get("x", 0), action.get("y", 0)
                # Check if click is near any tool button
                for tx, ty in tool_coords:
                    if abs(x - tx) < 40 and abs(y - ty) < 40:
                        tool_clicks += 1
                        break
            # Also check moveTo + click pattern (implicit click)
            elif action.get("action") == "moveTo" and i + 1 < len(actions):
                if actions[i + 1].get("action") == "click":
                    x, y = action.get("x", 0), action.get("y", 0)
                    for tx, ty in tool_coords:
                        if abs(x - tx) < 40 and abs(y - ty) < 40:
                            # Don't count here, will be counted by click itself
                            break

        return tool_clicks

    def _count_color_changes(self, actions):
        """Count number of color changes"""
        color_clicks = 0
        color_y = 25
        color_x_range = (405, 741)

        for action in actions:
            if action.get("action") == "click":
                x, y = action.get("x", 0), action.get("y", 0)
                if (color_x_range[0] <= x <= color_x_range[1] and
                    abs(y - color_y) < 20):
                    color_clicks += 1

        return color_clicks

    def _detect_exact_colors_used(self, actions):
        """
        ENHANCED: Detect which exact colors were selected
        Returns: List of color hex codes in order of selection
        """
        colors_used = []
        color_tolerance_x = 12
        color_tolerance_y = 8  # Tighter Y tolerance since all color buttons at same Y

        for i, action in enumerate(actions):
            # Check both click and moveTo+click patterns
            if action.get("action") == "click":
                x = action.get("x", 0)
                y = action.get("y", 0)

                # Find matching color
                for cx, cy, color in self.color_positions:
                    if (abs(x - cx) <= color_tolerance_x and
                        abs(y - cy) <= color_tolerance_y):
                        colors_used.append(color)
                        break

            # Check moveTo followed by click (without coordinates)
            elif action.get("action") == "moveTo":
                if i + 1 < len(actions) and actions[i + 1].get("action") == "click":
                    x = action.get("x", 0)
                    y = action.get("y", 0)

                    for cx, cy, color in self.color_positions:
                        if (abs(x - cx) <= color_tolerance_x and
                            abs(y - cy) <= color_tolerance_y):
                            colors_used.append(color)
                            break

        return colors_used

    def _estimate_canvas_coverage_accurate(self, actions):
        """
        ENHANCED: More accurate coverage using density grid method with tool-specific handling
        """
        grid_size = 20  # 20x20 grid = 400 cells
        grid = np.zeros((grid_size, grid_size), dtype=np.uint8)

        is_drawing = False
        current_tool = "pen"  # Default tool
        mouse_down_pos = None
        last_pos = (0, 0)  # Track last known position

        for i, action in enumerate(actions):
            # Update last position if action has coordinates
            if "x" in action and "y" in action:
                last_pos = (action.get("x"), action.get("y"))

            # Track tool selection
            if action.get("action") == "click" and "x" in action and "y" in action:
                x, y = action.get("x"), action.get("y")
                for tool_name, (tx, ty) in self.tool_positions.items():
                    if abs(x - tx) < 40 and abs(y - ty) < 40:
                        current_tool = tool_name
                        break
            elif action.get("action") == "moveTo":
                x, y = action.get("x", 0), action.get("y", 0)
                for tool_name, (tx, ty) in self.tool_positions.items():
                    if abs(x - tx) < 40 and abs(y - ty) < 40:
                        if i + 1 < len(actions) and actions[i + 1].get("action") == "click":
                            current_tool = tool_name
                        break

            if action.get("action") == "mouseDown":
                is_drawing = True
                # Use action coordinates if available, otherwise use last known position
                if "x" in action and "y" in action:
                    mouse_down_pos = (action.get("x"), action.get("y"))
                else:
                    mouse_down_pos = last_pos
            elif action.get("action") == "mouseUp":
                # Handle shape tools (rectangle, circle, line)
                if is_drawing and mouse_down_pos and current_tool in ["rectangle", "circle", "line"]:
                    # Use action coordinates if available, otherwise use last known position
                    if "x" in action and "y" in action:
                        mouse_up_pos = (action.get("x"), action.get("y"))
                    else:
                        mouse_up_pos = last_pos
                    self._fill_shape_in_grid(grid, grid_size, current_tool, mouse_down_pos, mouse_up_pos)
                is_drawing = False
                mouse_down_pos = None

            # For pen/eraser, track movement while drawing
            if is_drawing and current_tool in ["pen", "eraser"] and "x" in action and "y" in action:
                canvas_x = action["x"] - self.canvas_offset_x
                canvas_y = action["y"] - self.canvas_offset_y

                if (0 <= canvas_x <= self.canvas_width and
                    0 <= canvas_y <= self.canvas_height):

                    grid_x = int((canvas_x / self.canvas_width) * grid_size)
                    grid_y = int((canvas_y / self.canvas_height) * grid_size)
                    grid_x = min(grid_x, grid_size - 1)
                    grid_y = min(grid_y, grid_size - 1)
                    grid[grid_y, grid_x] = 1

        filled_cells = np.sum(grid)
        total_cells = grid_size * grid_size
        coverage = filled_cells / total_cells
        return round(coverage, 4)

    def _fill_shape_in_grid(self, grid, grid_size, tool, start_pos, end_pos):
        """Fill grid cells for shape tools (rectangle, circle, line)"""
        x1, y1 = start_pos
        x2, y2 = end_pos

        # Convert to canvas coordinates
        cx1 = x1 - self.canvas_offset_x
        cy1 = y1 - self.canvas_offset_y
        cx2 = x2 - self.canvas_offset_x
        cy2 = y2 - self.canvas_offset_y

        if tool == "rectangle":
            # Fill all cells in rectangle area
            min_x = min(cx1, cx2)
            max_x = max(cx1, cx2)
            min_y = min(cy1, cy2)
            max_y = max(cy1, cy2)

            # Convert pixel coordinates to grid cell coordinates
            min_gx = max(0, int((min_x / self.canvas_width) * grid_size))
            max_gx = min(grid_size - 1, int((max_x / self.canvas_width) * grid_size))
            min_gy = max(0, int((min_y / self.canvas_height) * grid_size))
            max_gy = min(grid_size - 1, int((max_y / self.canvas_height) * grid_size))

            # Fill all grid cells within the rectangle bounds
            for gx in range(min_gx, max_gx + 1):
                for gy in range(min_gy, max_gy + 1):
                    grid[gy, gx] = 1

        elif tool == "circle":
            # Calculate radius and fill circular area
            radius = np.sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)
            center_x, center_y = cx1, cy1

            # Fill cells within circle
            for angle in np.linspace(0, 2 * np.pi, 50):
                for r in np.linspace(0, radius, int(radius / 20) + 1):
                    x = center_x + r * np.cos(angle)
                    y = center_y + r * np.sin(angle)
                    if 0 <= x <= self.canvas_width and 0 <= y <= self.canvas_height:
                        gx = int((x / self.canvas_width) * grid_size)
                        gy = int((y / self.canvas_height) * grid_size)
                        gx = min(gx, grid_size - 1)
                        gy = min(gy, grid_size - 1)
                        grid[gy, gx] = 1

        elif tool == "line":
            # Draw line with thickness
            steps = int(max(abs(cx2 - cx1), abs(cy2 - cy1))) + 1
            for i in range(steps):
                t = i / max(steps - 1, 1)
                x = cx1 + t * (cx2 - cx1)
                y = cy1 + t * (cy2 - cy1)
                if 0 <= x <= self.canvas_width and 0 <= y <= self.canvas_height:
                    gx = int((x / self.canvas_width) * grid_size)
                    gy = int((y / self.canvas_height) * grid_size)
                    gx = min(gx, grid_size - 1)
                    gy = min(gy, grid_size - 1)
                    grid[gy, gx] = 1

    def _verify_tool_actually_used(self, actions, tool):
        """
        ENHANCED: Verify that tool was not just selected but actually used
        Returns: (was_selected, was_used)
        """
        if tool not in self.tool_positions:
            return False, False

        tx, ty = self.tool_positions[tool]
        tool_selected_idx = None

        # Find where tool was selected
        for i, action in enumerate(actions):
            # Pattern 1: moveTo + click
            if action.get("action") == "moveTo":
                x, y = action.get("x", 0), action.get("y", 0)
                if abs(x - tx) < 40 and abs(y - ty) < 40:
                    if i + 1 < len(actions) and actions[i + 1].get("action") == "click":
                        tool_selected_idx = i + 1
                        break
            # Pattern 2: click with coordinates
            elif action.get("action") == "click" and "x" in action:
                x, y = action.get("x", 0), action.get("y", 0)
                if abs(x - tx) < 40 and abs(y - ty) < 40:
                    tool_selected_idx = i
                    break

        if tool_selected_idx is None:
            return False, False

        # Check if tool was actually used (drawing action after selection)
        for i in range(tool_selected_idx + 1, len(actions)):
            action = actions[i]

            # If we find a drawing action, tool was used
            if action.get("action") == "mouseDown":
                return True, True

            # If another tool is selected before drawing, tool wasn't used
            if action.get("action") in ["moveTo", "click"]:
                x, y = action.get("x", 0), action.get("y", 0)
                # Check if this is selecting another tool
                for other_tool, (otx, oty) in self.tool_positions.items():
                    if other_tool != tool and abs(x - otx) < 40 and abs(y - oty) < 40:
                        return True, False  # Selected but not used

        # Tool selected but no drawing found
        return True, False

    def _count_drawing_segments(self, actions):
        """Count number of continuous drawing segments"""
        segments = 0
        in_segment = False

        for action in actions:
            if action.get("action") == "mouseDown":
                if not in_segment:
                    segments += 1
                    in_segment = True
            elif action.get("action") == "mouseUp":
                in_segment = False

        return segments

    def _estimate_canvas_coverage(self, actions):
        """Estimate how much of the canvas is covered"""
        # Collect all drawing positions
        positions = []
        is_drawing = False

        for action in actions:
            if action.get("action") == "mouseDown":
                is_drawing = True
            elif action.get("action") == "mouseUp":
                is_drawing = False

            if is_drawing and "x" in action and "y" in action:
                canvas_x = action["x"] - self.canvas_offset_x
                canvas_y = action["y"] - self.canvas_offset_y

                if (0 <= canvas_x <= self.canvas_width and
                    0 <= canvas_y <= self.canvas_height):
                    positions.append((canvas_x, canvas_y))

        if not positions:
            return 0.0

        # Calculate bounding box
        xs = [p[0] for p in positions]
        ys = [p[1] for p in positions]

        bbox_area = (max(xs) - min(xs)) * (max(ys) - min(ys))
        canvas_area = self.canvas_width * self.canvas_height

        coverage = bbox_area / canvas_area
        return round(coverage, 4)

    def _check_criteria(self, actions, criteria):
        """Check if specific criteria are met"""
        results = {}

        # Check required tools
        if "required_tools" in criteria:
            for tool in criteria["required_tools"]:
                tool_used = False
                if tool in self.tool_positions:
                    tx, ty = self.tool_positions[tool]
                    # Check for moveTo + click pattern OR direct click
                    for i, action in enumerate(actions):
                        # Pattern 1: moveTo tool position, then click
                        if action.get("action") == "moveTo":
                            x, y = action.get("x", 0), action.get("y", 0)
                            if abs(x - tx) < 40 and abs(y - ty) < 40:
                                # Check if next action is click
                                if i + 1 < len(actions) and actions[i + 1].get("action") == "click":
                                    tool_used = True
                                    break
                        # Pattern 2: click with coordinates
                        elif action.get("action") == "click" and "x" in action:
                            x, y = action.get("x", 0), action.get("y", 0)
                            if abs(x - tx) < 40 and abs(y - ty) < 40:
                                tool_used = True
                                break

                results[f"tool_{tool}_used"] = tool_used

                # ENHANCED: Tool usage verification
                was_selected, was_used = self._verify_tool_actually_used(actions, tool)
                results[f"tool_{tool}_selected"] = was_selected
                results[f"tool_{tool}_actually_used"] = was_used

        # Check minimum drawing segments
        if "min_segments" in criteria:
            actual_segments = self._count_drawing_segments(actions)
            results["min_segments_met"] = bool(actual_segments >= criteria["min_segments"])
            results["actual_segments"] = actual_segments

        # Check color usage
        if "required_colors" in criteria:
            # Old method: count clicks
            color_clicks = self._count_color_changes(actions)
            results["colors_changed"] = color_clicks
            results["min_colors_met"] = bool(color_clicks >= len(criteria["required_colors"]))

            # ENHANCED: Exact color detection
            exact_colors = self._detect_exact_colors_used(actions)
            required = set(criteria["required_colors"])
            used = set(exact_colors)

            matched_colors = required & used
            missing_colors = required - used

            results["colors_exact_used"] = list(used)
            results["colors_matched"] = len(matched_colors)
            results["colors_missing"] = list(missing_colors)
            results["min_colors_exact_met"] = bool(len(matched_colors) >= len(required))

        # Check canvas coverage
        if "min_coverage" in criteria:
            # Old method: bounding box
            coverage = self._estimate_canvas_coverage(actions)
            results["canvas_coverage"] = coverage
            results["min_coverage_met"] = bool(coverage >= criteria["min_coverage"])

            # ENHANCED: Accurate grid-based coverage
            accurate_coverage = self._estimate_canvas_coverage_accurate(actions)
            results["canvas_coverage_accurate"] = accurate_coverage
            results["min_coverage_accurate_met"] = bool(accurate_coverage >= criteria["min_coverage"])

        return results

    def _calculate_score(self, results):
        """Calculate overall score (0-1) with strict criteria penalties"""
        score = 1.0
        criteria_met = results.get('criteria_met', {})

        # STRICT PENALTIES FOR CRITERIA VIOLATIONS

        # ENHANCED: Tool penalties based on actual usage
        tool_penalties = 0
        for key, value in criteria_met.items():
            # Prefer "actually_used" over just "used"
            if key.endswith('_actually_used'):
                if not value:
                    tool_penalties += 0.15  # Reduced from 0.20 to prevent score saturation
            elif key.startswith('tool_') and key.endswith('_used'):
                # Only penalize if there's no "actually_used" check
                tool_name = key.replace('tool_', '').replace('_used', '')
                if f'tool_{tool_name}_actually_used' not in criteria_met:
                    if not value:
                        tool_penalties += 0.15  # Reduced from 0.20 to prevent score saturation
        score -= tool_penalties

        # ENHANCED: Exact color matching penalty
        if criteria_met.get('min_colors_exact_met') is not None:
            # Use exact color matching if available
            if not criteria_met.get('min_colors_exact_met', True):
                colors_required = results.get('colors_required', 0)
                colors_matched = criteria_met.get('colors_matched', 0)
                missing_colors = max(0, colors_required - colors_matched)
                score -= 0.05 * missing_colors  # Reduced from 0.08 to prevent score saturation
        else:
            # Fallback to old method if exact matching not available
            if not criteria_met.get('min_colors_met', True):
                colors_required = results.get('colors_required', 0)
                colors_used = criteria_met.get('colors_changed', 0)
                missing_colors = max(0, colors_required - colors_used)
                score -= 0.05 * missing_colors  # Reduced from 0.08 to prevent score saturation

        # Insufficient drawing segments: -0.15
        if not criteria_met.get('min_segments_met', True):
            score -= 0.15

        # ENHANCED: Proportional coverage penalty based on deficit
        if criteria_met.get('min_coverage_accurate_met') is not None:
            if not criteria_met.get('min_coverage_accurate_met', True):
                # Get actual coverage and required coverage
                actual_coverage = results['metrics'].get('canvas_coverage_accurate', 0)
                required_coverage = results.get('min_coverage', 0)

                if required_coverage > 0:
                    # Calculate deficit ratio (how far below requirement)
                    deficit = max(0, required_coverage - actual_coverage)
                    deficit_ratio = deficit / required_coverage
                    # Proportional penalty: full 0.12 if 0% coverage, scales down as coverage increases
                    score -= deficit_ratio * 0.12
                else:
                    # No requirement, no penalty
                    pass
        else:
            # Fallback to old method (binary)
            if not criteria_met.get('min_coverage_met', True):
                score -= 0.12

        # Errors and warnings
        error_penalty = len(results["errors"]) * 0.08
        warning_penalty = len(results["warnings"]) * 0.02

        score -= error_penalty
        score -= warning_penalty

        # Small bonus for reasonable action count (only if some criteria met)
        action_count = results["total_actions"]
        if 10 <= action_count <= 500 and score >= 0.2:
            score += 0.05

        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, round(score, 3)))

    def _extract_spatial_constraints(self, prompt):
        """Extract spatial constraints from prompt text"""
        if not prompt:
            return {}

        prompt_lower = prompt.lower()
        constraints = {}

        # Detect region constraints
        if 'top-left' in prompt_lower or 'upper-left' in prompt_lower or 'top left' in prompt_lower:
            constraints['region'] = 'top-left'
        elif 'top-right' in prompt_lower or 'upper-right' in prompt_lower or 'top right' in prompt_lower:
            constraints['region'] = 'top-right'
        elif 'bottom-left' in prompt_lower or 'lower-left' in prompt_lower or 'bottom left' in prompt_lower:
            constraints['region'] = 'bottom-left'
        elif 'bottom-right' in prompt_lower or 'lower-right' in prompt_lower or 'bottom right' in prompt_lower:
            constraints['region'] = 'bottom-right'
        elif 'center' in prompt_lower or 'middle' in prompt_lower or 'centre' in prompt_lower:
            constraints['region'] = 'center'
        elif 'top' in prompt_lower or 'upper' in prompt_lower:
            constraints['region'] = 'top'
        elif 'bottom' in prompt_lower or 'lower' in prompt_lower:
            constraints['region'] = 'bottom'
        elif 'left' in prompt_lower:
            constraints['region'] = 'left'
        elif 'right' in prompt_lower:
            constraints['region'] = 'right'

        return constraints

    def _calculate_drawing_centroid(self, actions):
        """Calculate centroid of all drawing points"""
        drawing_points = []
        is_drawing = False
        current_pos = None

        for action in actions:
            action_type = action.get('action', '')
            x = action.get('x')
            y = action.get('y')

            if action_type == 'moveTo' and x is not None and y is not None:
                current_pos = (x, y)

            elif action_type == 'mouseDown' and current_pos:
                is_drawing = True
                # Check if on canvas
                if (self.canvas_offset_x <= current_pos[0] < self.canvas_offset_x + self.canvas_width and
                    self.canvas_offset_y <= current_pos[1] < self.canvas_offset_y + self.canvas_height):
                    drawing_points.append(current_pos)

            elif action_type == 'mouseUp':
                is_drawing = False

            elif is_drawing and action_type == 'moveTo' and x is not None and y is not None:
                # Drawing in progress, add point
                if (self.canvas_offset_x <= x < self.canvas_offset_x + self.canvas_width and
                    self.canvas_offset_y <= y < self.canvas_offset_y + self.canvas_height):
                    drawing_points.append((x, y))

        if not drawing_points:
            return None

        # Calculate centroid
        avg_x = sum(p[0] for p in drawing_points) / len(drawing_points)
        avg_y = sum(p[1] for p in drawing_points) / len(drawing_points)

        # Convert to canvas-relative coordinates
        rel_x = avg_x - self.canvas_offset_x
        rel_y = avg_y - self.canvas_offset_y

        return (rel_x, rel_y)

    def _evaluate_spatial_accuracy(self, actions, constraints):
        """Evaluate spatial accuracy against constraints"""
        if not constraints or 'region' not in constraints:
            return None

        centroid = self._calculate_drawing_centroid(actions)
        if centroid is None:
            return 0.0  # No drawing, no accuracy

        cx, cy = centroid
        region = constraints['region']

        # Define region boundaries (canvas-relative)
        # Divide canvas into 3x3 grid for regions
        third_w = self.canvas_width / 3
        third_h = self.canvas_height / 3

        region_centers = {
            'top-left': (third_w / 2, third_h / 2),
            'top': (self.canvas_width / 2, third_h / 2),
            'top-right': (self.canvas_width - third_w / 2, third_h / 2),
            'left': (third_w / 2, self.canvas_height / 2),
            'center': (self.canvas_width / 2, self.canvas_height / 2),
            'right': (self.canvas_width - third_w / 2, self.canvas_height / 2),
            'bottom-left': (third_w / 2, self.canvas_height - third_h / 2),
            'bottom': (self.canvas_width / 2, self.canvas_height - third_h / 2),
            'bottom-right': (self.canvas_width - third_w / 2, self.canvas_height - third_h / 2)
        }

        if region not in region_centers:
            return None

        target_x, target_y = region_centers[region]

        # Calculate distance from centroid to region center
        distance = ((cx - target_x) ** 2 + (cy - target_y) ** 2) ** 0.5

        # Maximum possible distance (canvas diagonal)
        max_distance = (self.canvas_width ** 2 + self.canvas_height ** 2) ** 0.5

        # Normalize to [0, 1] - higher is better
        spatial_accuracy = max(0.0, 1.0 - (distance / max_distance))

        return spatial_accuracy

    def _calculate_action_efficiency(self, actions, criteria):
        """Calculate action efficiency based on task complexity"""
        actual_action_count = len(actions)

        # Estimate minimum actions needed for this task
        min_actions = 0

        # Tool selections (1 action per required tool)
        if 'required_tools' in criteria:
            min_actions += len(criteria['required_tools'])

        # Color selections (1 action per required color)
        if 'required_colors' in criteria:
            min_actions += len(criteria['required_colors'])

        # Drawing actions (3 per segment: moveTo, mouseDown, mouseUp minimum)
        if 'min_segments' in criteria:
            min_actions += criteria['min_segments'] * 3

        # If no criteria, cannot calculate efficiency
        if min_actions == 0:
            return None

        # Calculate efficiency score based on ratio
        # Excellent: <= 1.5x minimum
        # Good: <= 2.0x minimum
        # Acceptable: <= 3.0x minimum
        # Inefficient: > 3.0x minimum

        ratio = actual_action_count / min_actions

        if ratio <= 1.5:
            efficiency = 1.0  # Excellent
        elif ratio <= 2.0:
            efficiency = 0.8  # Good
        elif ratio <= 3.0:
            efficiency = 0.6  # Acceptable
        else:
            efficiency = 0.4  # Inefficient

        return round(efficiency, 3)

    def _classify_errors(self, results, criteria):
        """Classify errors into categories for detailed analysis"""
        error_classification = {
            'spatial_errors': [],
            'tool_errors': [],
            'color_errors': [],
            'planning_errors': [],
            'syntax_errors': []
        }

        if not criteria:
            return error_classification

        # Tool errors
        criteria_met = results.get('criteria_met', {})
        for key in criteria_met:
            if key.endswith('_actually_used') and not criteria_met[key]:
                tool_name = key.replace('tool_', '').replace('_actually_used', '')
                error_classification['tool_errors'].append({
                    'type': 'missing_required_tool',
                    'tool': tool_name
                })

        # Color errors
        if 'required_colors' in criteria:
            exact_colors_used = results['metrics'].get('exact_colors_used', [])
            for color in criteria['required_colors']:
                if color not in exact_colors_used:
                    error_classification['color_errors'].append({
                        'type': 'missing_required_color',
                        'color': color
                    })

        # Coverage errors (spatial)
        if 'min_coverage' in criteria:
            actual_coverage = results['metrics'].get('canvas_coverage_accurate', 0)
            required_coverage = criteria['min_coverage']
            if actual_coverage < required_coverage:
                error_classification['spatial_errors'].append({
                    'type': 'insufficient_coverage',
                    'actual': actual_coverage,
                    'required': required_coverage,
                    'deficit': required_coverage - actual_coverage
                })

        # Segments errors (planning)
        if 'min_segments' in criteria:
            actual_segments = results['metrics'].get('drawing_segments', 0)
            required_segments = criteria['min_segments']
            if actual_segments < required_segments:
                error_classification['planning_errors'].append({
                    'type': 'insufficient_segments',
                    'actual': actual_segments,
                    'required': required_segments,
                    'deficit': required_segments - actual_segments
                })

        # Spatial accuracy errors
        spatial_accuracy = results['metrics'].get('spatial_accuracy')
        if spatial_accuracy is not None and spatial_accuracy < 0.7:
            spatial_constraints = results['metrics'].get('spatial_constraints', {})
            error_classification['spatial_errors'].append({
                'type': 'incorrect_spatial_placement',
                'accuracy': spatial_accuracy,
                'expected_region': spatial_constraints.get('region')
            })

        # Syntax errors from evaluator
        for error in results.get('errors', []):
            error_classification['syntax_errors'].append(error)

        return error_classification

    def generate_feedback(self, evaluation_results):
        """Generate human-readable feedback from evaluation results"""
        feedback = []

        # Report errors
        if evaluation_results["errors"]:
            feedback.append("ERRORS FOUND:")
            for error in evaluation_results["errors"][:5]:  # Show first 5
                feedback.append(f"  - [{error['type']}] {error['message']}")

        # Report warnings
        if evaluation_results["warnings"]:
            feedback.append("\nWARNINGS:")
            for warning in evaluation_results["warnings"][:3]:
                feedback.append(f"  - [{warning['type']}] {warning['message']}")

        # Report metrics
        feedback.append("\nMETRICS:")
        feedback.append(f"  - Total actions: {evaluation_results['total_actions']}")
        feedback.append(f"  - Tool changes: {evaluation_results['metrics']['tool_changes']}")
        feedback.append(f"  - Color changes: {evaluation_results['metrics']['color_changes']}")
        feedback.append(f"  - Drawing segments: {evaluation_results['metrics']['drawing_segments']}")
        feedback.append(f"  - Canvas coverage: {evaluation_results['metrics']['canvas_coverage']:.2%}")

        # Report criteria
        if "criteria_met" in evaluation_results:
            feedback.append("\nCRITERIA:")
            for key, value in evaluation_results["criteria_met"].items():
                status = "PASS" if value else "FAIL"
                feedback.append(f"  - {key}: {status}")

        # Overall score
        feedback.append(f"\nOVERALL SCORE: {evaluation_results['score']:.2f}/1.00")

        return "\n".join(feedback)


def evaluate_from_file(actions_file, criteria_file=None):
    """Evaluate actions from a JSON file"""
    with open(actions_file, 'r') as f:
        actions = json.load(f)

    criteria = None
    if criteria_file:
        with open(criteria_file, 'r') as f:
            criteria = json.load(f)

    evaluator = DrawingEvaluator()
    results = evaluator.evaluate(actions, criteria=criteria)

    return results


if __name__ == "__main__":
    # Example usage
    test_actions = [
        {"action": "moveTo", "x": 453, "y": 25},
        {"action": "click"},
        {"action": "moveTo", "x": 245, "y": 25},
        {"action": "click"},
        {"action": "moveTo", "x": 590, "y": 420},
        {"action": "mouseDown"},
        {"action": "moveTo", "x": 640, "y": 420},
        {"action": "moveTo", "x": 665, "y": 445},
        {"action": "moveTo", "x": 665, "y": 495},
        {"action": "mouseUp"}
    ]

    test_criteria = {
        "required_tools": ["pen"],
        "min_segments": 1,
        "required_colors": ["#FF0000"],
        "min_coverage": 0.01
    }

    evaluator = DrawingEvaluator()
    results = evaluator.evaluate(test_actions, criteria=test_criteria)

    print("="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(evaluator.generate_feedback(results))
    print("="*60)
