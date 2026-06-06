import sys
from typing import Dict, Any, Set
from novalang.vm import VirtualMachine, VMObject

class VMDebugger:
    def __init__(self, bytecode: dict):
        self.bytecode = bytecode
        self.vm = VirtualMachine()
        self.breakpoints: Set[int] = set()

    def run(self):
        print("NovaLang Bytecode VM Debugger (v1.3.0)")
        print("Type 'help' or 'h' for list of debugger commands.")
        
        self.vm.init_execution(self.bytecode)
        
        if not self.vm.frames:
            print("No main instructions found to debug.")
            return

        while True:
            if not self.vm.frames:
                print("Program terminated.")
                break
                
            frame = self.vm.frames[-1]
            pc = frame.pc
            
            if pc >= len(frame.instructions):
                # Pop frame
                self.vm.step()
                continue
                
            instr = frame.instructions[pc]
            print(f"\n-> [{frame.name}] PC {pc}: {instr[0]} {instr[1:] if len(instr) > 1 else ''}")
            
            try:
                cmd_line = input("(nova-dbg) ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nExiting debugger.")
                break
                
            if not cmd_line:
                continue
                
            parts = cmd_line.split()
            cmd = parts[0]
            
            if cmd in ("help", "h"):
                self.print_help()
                
            elif cmd in ("step", "s"):
                self.vm.step()
                
            elif cmd in ("continue", "c"):
                # Run until halt or breakpoint
                terminated = False
                while True:
                    self.vm.step()
                    if not self.vm.frames:
                        print("Program terminated.")
                        terminated = True
                        break
                        
                    curr_frame = self.vm.frames[-1]
                    curr_pc = curr_frame.pc
                    # Check breakpoint
                    if curr_frame.name == "main" and curr_pc in self.breakpoints:
                        print(f"\n[Breakpoint] Hit breakpoint at PC {curr_pc}")
                        break
                if terminated:
                    break
                    
            elif cmd in ("break", "b"):
                if len(parts) < 2:
                    print("Error: Missing PC index. Usage: break <pc>")
                    continue
                try:
                    target_pc = int(parts[1])
                    self.breakpoints.add(target_pc)
                    print(f"Breakpoint set at main PC {target_pc}")
                except ValueError:
                    print("Error: Invalid PC index. Must be an integer.")
                    
            elif cmd in ("stack", "p"):
                stack_vals = []
                for val in self.vm.operand_stack:
                    if isinstance(val, VMObject):
                        stack_vals.append(f"{val.type_name}({val.value})")
                    else:
                        stack_vals.append(repr(val))
                print(f"Stack: {stack_vals}")
                
            elif cmd in ("locals", "l"):
                local_vals = {}
                for k, v in frame.locals.items():
                    local_vals[k] = v.value if isinstance(v, VMObject) else v
                print(f"Locals: {local_vals}")
                
            elif cmd in ("globals", "g"):
                global_vals = {}
                for k, v in self.vm.globals.items():
                    global_vals[k] = v.value if isinstance(v, VMObject) else v
                print(f"Globals: {global_vals}")
                
            elif cmd in ("list", "v"):
                start = max(0, pc - 5)
                end = min(len(frame.instructions), pc + 6)
                for idx in range(start, end):
                    prefix = "=>" if idx == pc else "  "
                    curr_instr = frame.instructions[idx]
                    print(f"{prefix} {idx:3d}: {curr_instr[0]} {curr_instr[1:] if len(curr_instr) > 1 else ''}")
                    
            elif cmd in ("exit", "q"):
                print("Exiting debugger.")
                break
                
            else:
                print(f"Unknown command: '{cmd}'. Type 'help' for instructions.")

    def print_help(self):
        help_text = """NovaLang Debugger Commands:
  step, s         Execute exactly one instruction
  continue, c     Resume program execution
  break, b <pc>   Set breakpoint at specific PC in main frame
  stack, p        Print elements on operand stack
  locals, l       Print active local frame variables
  globals, g      Print global variables
  list, v         Display surrounding instructions
  help, h         Print this menu
  exit, q         Exit debugger
"""
        print(help_text)
