class CPU:
    _instance = None
    
    def __init__(self):
        if CPU._instance is not None:
            raise Exception("CPU is a singleton class. Use get_instance() method.")
        
        self.reset()
        
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CPU()
        return cls._instance
    
    def reset(self):
        # 16-bit registers
        self.AX = 0x0000
        self.BX = 0x0000
        self.CX = 0x0000
        self.DX = 0x0000
        self.SI = 0x0000
        self.DI = 0x0000
        self.SP = 0xFFFE
        self.BP = 0x0000
        self.IP = 0x0000
        self.CS = 0x0000
        self.DS = 0x0000
        self.ES = 0x0000
        self.SS = 0x0000
        
        # Flags
        self.CF = False
        self.PF = False
        self.AF = False
        self.ZF = False
        self.SF = False
        self.TF = False
        self.IF = False
        self.DF = False
        self.OF = False
        
        # Memory (1MB address space)
        self.memory = bytearray(1024 * 1024)
        self.code = []
        self.code_labels = {}
        self.running = False
        self.halted = False
        self.current_instruction = None
        self.microinstructions = []
        
    def load_code(self, code):
        self.reset()
        self.code = self._parse_code(code)
        
    def _parse_code(self, code):
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        parsed = []
        
        for line in lines:
            if ':' in line:
                label, instruction = line.split(':', 1)
                self.code_labels[label.strip()] = len(parsed)
                line = instruction.strip()
            if line:
                parsed.append(line)
        return parsed
    
    def step(self):
        if self.halted or self.IP >= len(self.code):
            self.halted = True
            return False
            
        self.current_instruction = self.code[self.IP]
        self.microinstructions = self._decode_instruction(self.current_instruction)
        
        # Execute all microinstructions
        for microinstr in self.microinstructions:
            if hasattr(microinstr, 'execute'):
                microinstr.execute(self)
        
        self.IP += 1
        return True
        
    def run(self):
        self.running = True
        while not self.halted and self.running and self.IP < len(self.code):
            self.step()
            
    def _decode_instruction(self, instruction):
        from app.simulator.instruction_set import InstructionSet
        return InstructionSet.decode(instruction)
    
    def read_memory(self, address, size=2):
        """Read 16-bit value from memory (little-endian)"""
        address = address & 0xFFFFF  # Ensure valid address
        return int.from_bytes(self.memory[address:address+size], 'little')
    
    def write_memory(self, address, value, size=2):
        """Write 16-bit value to memory (little-endian)"""
        address = address & 0xFFFFF  # Ensure valid address
        self.memory[address:address+size] = value.to_bytes(size, 'little')
    
    def get_state(self):
        return {
            'registers': {
                'AX': self.AX,
                'BX': self.BX,
                'CX': self.CX,
                'DX': self.DX,
                'SI': self.SI,
                'DI': self.DI,
                'SP': self.SP,
                'BP': self.BP,
                'IP': self.IP,
                'CS': self.CS,
                'DS': self.DS,
                'ES': self.ES,
                'SS': self.SS,
                'AH': (self.AX >> 8) & 0xFF,
                'AL': self.AX & 0xFF,
                'BH': (self.BX >> 8) & 0xFF,
                'BL': self.BX & 0xFF,
                'CH': (self.CX >> 8) & 0xFF,
                'CL': self.CX & 0xFF,
                'DH': (self.DX >> 8) & 0xFF,
                'DL': self.DX & 0xFF,
            },
            'flags': {
                'CF': self.CF,
                'PF': self.PF,
                'AF': self.AF,
                'ZF': self.ZF,
                'SF': self.SF,
                'TF': self.TF,
                'IF': self.IF,
                'DF': self.DF,
                'OF': self.OF,
            },
            'memory': list(self.memory[:256]),  # First 256 bytes for display
            'current_instruction': self.current_instruction,
            'microinstructions': [str(m) for m in self.microinstructions],
            'status': 'running' if self.running and not self.halted else 'halted',
            'ip': self.IP,
        }