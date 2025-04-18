class Microinstruction:
    def __init__(self, description):
        self.description = description

    def execute(self, cpu):
        pass

    def __str__(self):
        return self.description


class MoveRegToReg(Microinstruction):
    def __init__(self, dest, src):
        super().__init__(f"MOV {dest}, {src}")
        self.dest = dest
        self.src = src

    def execute(self, cpu):
        value = getattr(cpu, self.src)
        setattr(cpu, self.dest, value)


class MoveImmToReg(Microinstruction):
    def __init__(self, dest, value):
        super().__init__(f"MOV {dest}, {hex(value)}")
        self.dest = dest
        self.value = value

    def execute(self, cpu):
        setattr(cpu, self.dest, self.value & 0xFFFF)


class MoveMemToReg(Microinstruction):
    def __init__(self, dest, address):
        super().__init__(f"MOV {dest}, [{hex(address)}]")
        self.dest = dest
        self.address = address

    def execute(self, cpu):
        value = cpu.read_memory(self.address)
        setattr(cpu, self.dest, value)


class MoveRegToMem(Microinstruction):
    def __init__(self, src, address):
        super().__init__(f"MOV [{hex(address)}], {src}")
        self.src = src
        self.address = address

    def execute(self, cpu):
        value = getattr(cpu, self.src)
        cpu.write_memory(self.address, value)


class AddRegToReg(Microinstruction):
    def __init__(self, dest, src):
        super().__init__(f"ADD {dest}, {src}")
        self.dest = dest
        self.src = src

    def execute(self, cpu):
        a = getattr(cpu, self.dest)
        b = getattr(cpu, self.src)
        result = a + b

        cpu.CF = result > 0xFFFF
        cpu.PF = bin(result & 0xFF).count('1') % 2 == 0
        cpu.AF = (a & 0xF) + (b & 0xF) > 0xF
        cpu.ZF = (result & 0xFFFF) == 0
        cpu.SF = (result & 0x8000) != 0
        cpu.OF = ((a ^ result) & (b ^ result) & 0x8000) != 0

        setattr(cpu, self.dest, result & 0xFFFF)


class SubRegFromReg(Microinstruction):
    def __init__(self, dest, src):
        super().__init__(f"SUB {dest}, {src}")
        self.dest = dest
        self.src = src

    def execute(self, cpu):
        a = getattr(cpu, self.dest)
        b = getattr(cpu, self.src)
        result = a - b

        cpu.CF = result < 0
        cpu.PF = bin(result & 0xFF).count('1') % 2 == 0
        cpu.AF = (a & 0xF) < (b & 0xF)
        cpu.ZF = (result & 0xFFFF) == 0
        cpu.SF = (result & 0x8000) != 0
        cpu.OF = ((a ^ b) & (a ^ result) & 0x8000) != 0

        setattr(cpu, self.dest, result & 0xFFFF)


class MulReg(Microinstruction):
    def __init__(self, src):
        super().__init__(f"MUL {src}")
        self.src = src

    def execute(self, cpu):
        value = getattr(cpu, self.src)
        result = cpu.AX * value
        cpu.AX = result & 0xFFFF
        cpu.DX = (result >> 16) & 0xFFFF
        cpu.CF = cpu.OF = cpu.DX != 0


class DivReg(Microinstruction):
    def __init__(self, src):
        super().__init__(f"DIV {src}")
        self.src = src

    def execute(self, cpu):
        divisor = getattr(cpu, self.src)
        if divisor == 0:
            raise ZeroDivisionError("Division by zero")
        dividend = (cpu.DX << 16) | cpu.AX
        cpu.AX = dividend // divisor
        cpu.DX = dividend % divisor


class CmpRegToReg(Microinstruction):
    def __init__(self, reg1, reg2):
        super().__init__(f"CMP {reg1}, {reg2}")
        self.reg1 = reg1
        self.reg2 = reg2

    def execute(self, cpu):
        a = getattr(cpu, self.reg1)
        b = getattr(cpu, self.reg2)
        result = a - b
        cpu.ZF = (result & 0xFFFF) == 0
        cpu.SF = (result & 0x8000) != 0
        cpu.CF = a < b
        cpu.OF = ((a ^ b) & (a ^ result) & 0x8000) != 0


class JmpLabel(Microinstruction):
    def __init__(self, address):
        super().__init__(f"JMP {hex(address)}")
        self.address = address

    def execute(self, cpu):
        cpu.IP = self.address


class JzLabel(Microinstruction):
    def __init__(self, address):
        super().__init__(f"JZ {hex(address)}")
        self.address = address

    def execute(self, cpu):
        if cpu.ZF:
            cpu.IP = self.address


class JnzLabel(Microinstruction):
    def __init__(self, address):
        super().__init__(f"JNZ {hex(address)}")
        self.address = address

    def execute(self, cpu):
        if not cpu.ZF:
            cpu.IP = self.address


class InstructionSet:
    @staticmethod
    def decode(instruction):
        parts = [p.strip() for p in instruction.split(maxsplit=1)]
        if not parts:
            return []

        op = parts[0].upper()
        operands = parts[1].split(',') if len(parts) > 1 else []

        try:
            if op == 'MOV' and len(operands) == 2:
                dest = operands[0].strip()
                src = operands[1].strip()
                if src.isdigit():
                    return [MoveImmToReg(dest, int(src))]
                elif src.upper() in ['AX', 'BX', 'CX', 'DX', 'SI', 'DI', 'SP', 'BP']:
                    return [MoveRegToReg(dest, src.upper())]
                elif src.startswith('[') and src.endswith(']'):
                    address = int(src[1:-1].strip(), 16)
                    return [MoveMemToReg(dest, address)]
                elif dest.startswith('[') and dest.endswith(']'):
                    address = int(dest[1:-1].strip(), 16)
                    return [MoveRegToMem(src.upper(), address)]

            elif op == 'ADD' and len(operands) == 2:
                dest = operands[0].strip()
                src = operands[1].strip()
                if src.upper() in ['AX', 'BX', 'CX', 'DX', 'SI', 'DI', 'SP', 'BP']:
                    return [AddRegToReg(dest, src.upper())]
                elif src.isdigit():
                    return [MoveImmToReg('TEMP', int(src)), AddRegToReg(dest, 'TEMP')]

            elif op == 'SUB' and len(operands) == 2:
                dest = operands[0].strip()
                src = operands[1].strip()
                if src.upper() in ['AX', 'BX', 'CX', 'DX', 'SI', 'DI', 'SP', 'BP']:
                    return [SubRegFromReg(dest, src.upper())]
                elif src.isdigit():
                    return [MoveImmToReg('TEMP', int(src)), SubRegFromReg(dest, 'TEMP')]

            elif op == 'MUL' and len(operands) == 1:
                return [MulReg(operands[0].strip().upper())]

            elif op == 'DIV' and len(operands) == 1:
                return [DivReg(operands[0].strip().upper())]

            elif op == 'CMP' and len(operands) == 2:
                return [CmpRegToReg(operands[0].strip().upper(), operands[1].strip().upper())]

            elif op == 'JMP' and len(operands) == 1:
                return [JmpLabel(int(operands[0].strip(), 16))]

            elif op == 'JZ' and len(operands) == 1:
                return [JzLabel(int(operands[0].strip(), 16))]

            elif op == 'JNZ' and len(operands) == 1:
                return [JnzLabel(int(operands[0].strip(), 16))]

        except Exception as e:
            return [Microinstruction(f"Error: {str(e)}")]

        return [Microinstruction(f"Unimplemented: {instruction}")]
