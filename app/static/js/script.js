document.addEventListener('DOMContentLoaded', function () {
    const loadBtn = document.getElementById('load-btn');
    const resetBtn = document.getElementById('reset-btn');
    const stepBtn = document.getElementById('step-btn');
    const runBtn = document.getElementById('run-btn');
    const exportJsonBtn = document.getElementById('export-json');
    const exportPdfBtn = document.getElementById('export-pdf');
    const registersDisplay = document.getElementById('registers-display');
    const flagsDisplay = document.getElementById('flags-display');
    const currentInstructionDisplay = document.getElementById('current-instruction');
    const microinstructionsDisplay = document.getElementById('microinstructions');
    const memoryDisplay = document.getElementById('memory-display');

    // Initialize display elements
    initRegisterDisplay();
    initFlagsDisplay();

    // Export as JSON
    exportJsonBtn.addEventListener('click', () => {
        const currentData = {
            code: window.editor.getValue(),
            registers: getRegistersData(),
            flags: getFlagsData(),
            currentInstruction: currentInstructionDisplay.textContent,
            microinstructions: Array.from(microinstructionsDisplay.children).map(div => div.textContent),
            memory: extractMemoryData()
        };
        const jsonStr = JSON.stringify(currentData, null, 2);
        const blob = new Blob([jsonStr], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'simulation-report.json';
        link.click();
    });

    // Export as PDF
    exportPdfBtn.addEventListener('click', () => {
        const doc = new jsPDF();
        doc.setFontSize(12);
        doc.text('8086 Architecture Simulation Report', 20, 10);

        const currentData = {
            code: window.editor.getValue(),
            registers: getRegistersData(),
            flags: getFlagsData(),
            currentInstruction: currentInstructionDisplay.textContent,
            microinstructions: Array.from(microinstructionsDisplay.children).map(div => div.textContent),
            memory: extractMemoryData()
        };

        doc.text(JSON.stringify(currentData, null, 2), 20, 20);
        doc.save('simulation-report.pdf');
    });

    function getRegistersData() {
        const registers = {};
        document.querySelectorAll('.register').forEach(el => {
            const regName = el.dataset.name;
            const regValue = el.querySelector('.register-value').textContent;
            registers[regName] = regValue;
        });
        return registers;
    }

    function getFlagsData() {
        const flags = {};
        document.querySelectorAll('.flag').forEach(el => {
            const flagName = el.dataset.name;
            const flagValue = el.querySelector('.flag-value').textContent;
            flags[flagName] = flagValue;
        });
        return flags;
    }

    function extractMemoryData() {
        const memory = [];
        memoryDisplay.querySelectorAll('.memory-table tr').forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length > 1) {
                const memoryRow = Array.from(cells).map(cell => cell.textContent);
                memory.push(memoryRow);
            }
        });
        return memory;
    }

    // Functions for Monaco editor operations
    loadBtn.addEventListener('click', () => sendCommand('load', window.editor.getValue()));
    resetBtn.addEventListener('click', () => sendCommand('reset'));
    stepBtn.addEventListener('click', () => sendCommand('step'));
    runBtn.addEventListener('click', () => sendCommand('run'));

    async function sendCommand(action, code = '') {
        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action, code })
            });

            const data = await response.json();
            if (data.success) {
                updateUI(data);
            } else {
                console.error('Error:', data.error);
                alert('Error: ' + data.error);
            }
        } catch (err) {
            console.error('Fetch error:', err);
            alert('Network error: ' + err.message);
        }
    }

    // Initialize Registers and Flags Display
    function initRegisterDisplay() {
        const registers = [
            'AX', 'AH', 'AL', 'BX', 'BH', 'BL',
            'CX', 'CH', 'CL', 'DX', 'DH', 'DL',
            'SI', 'DI', 'SP', 'BP', 'IP',
            'CS', 'DS', 'ES', 'SS'
        ];

        registersDisplay.innerHTML = '';
        registers.forEach(reg => {
            const div = document.createElement('div');
            div.className = 'register';
            div.dataset.name = reg;
            div.innerHTML = `
                <span class="register-name">${reg}</span>
                <span class="register-value">0x0000 (0)</span>
            `;
            registersDisplay.appendChild(div);
        });
    }

    function initFlagsDisplay() {
        const flags = ['CF', 'PF', 'AF', 'ZF', 'SF', 'OF', 'DF', 'IF', 'TF'];
        flagsDisplay.innerHTML = '';
        flags.forEach(flag => {
            const div = document.createElement('div');
            div.className = 'flag';
            div.dataset.name = flag;
            div.innerHTML = `
                <span class="flag-name">${flag}</span>
                <span class="flag-value">0</span>
            `;
            flagsDisplay.appendChild(div);
        });
    }

    function updateUI(data) {
        if (data.registers) {
            for (const [reg, value] of Object.entries(data.registers)) {
                const el = document.querySelector(`.register[data-name="${reg}"] .register-value`);
                if (el) el.textContent = value;
            }
        }

        if (data.flags) {
            for (const [flag, value] of Object.entries(data.flags)) {
                const el = document.querySelector(`.flag[data-name="${flag}"] .flag-value`);
                if (el) el.textContent = value ? '1' : '0';
            }
        }

        currentInstructionDisplay.textContent = data.current_instruction || 'No instruction loaded';

        microinstructionsDisplay.innerHTML = '';
        if (Array.isArray(data.microinstructions)) {
            data.microinstructions.forEach(micro => {
                const div = document.createElement('div');
                div.className = 'microinstruction';
                div.textContent = micro;
                microinstructionsDisplay.appendChild(div);
            });
        }

        if (data.memory) {
            updateMemoryDisplay(data.memory);
        }
    }

    function updateMemoryDisplay(memory) {
        memoryDisplay.innerHTML = '<h3>Memory (First 256 bytes)</h3>';
        const table = document.createElement('table');
        table.className = 'memory-table';
        const header = document.createElement('tr');
        header.innerHTML = '<th>Address</th><th>+0</th><th>+1</th><th>+2</th><th>+3</th><th>ASCII</th>';
        table.appendChild(header);

        for (let i = 0; i < 16; i++) {
            const row = document.createElement('tr');
            const addr = i * 16;
            const bytes = memory.slice(addr, addr + 16);

            let ascii = '';
            let cells = `<td>0x${addr.toString(16).toUpperCase().padStart(4, '0')}</td>`;

            for (let j = 0; j < 4; j++) {
                const byte1 = bytes[j * 2] || 0;
                const byte2 = bytes[j * 2 + 1] || 0;
                cells += `<td>${byte1.toString(16).padStart(2, '0')} ${byte2.toString(16).padStart(2, '0')}</td>`;
                ascii += (byte1 >= 32 && byte1 < 127 ? String.fromCharCode(byte1) : '.') +
                         (byte2 >= 32 && byte2 < 127 ? String.fromCharCode(byte2) : '.');
            }

            row.innerHTML = `${cells}<td>${ascii}</td>`;
            table.appendChild(row);
        }

        memoryDisplay.appendChild(table);
    }
});
