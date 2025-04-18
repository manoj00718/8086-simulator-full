from flask import Blueprint, render_template, request, jsonify
from app.simulator.cpu import CPU

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST' and request.is_json:
        data = request.get_json()
        cpu = CPU.get_instance()
        response = {'success': True}
        
        try:
            if data.get('action') == 'reset':
                cpu.reset()
            elif data.get('action') == 'step':
                if not cpu.step():
                    response['status'] = 'halted'
            elif data.get('action') == 'run':
                cpu.run()
            elif data.get('action') == 'load':
                cpu.load_code(data.get('code', ''))
            
            response.update(cpu.get_state())
            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                **cpu.get_state()
            })
    
    return render_template('index.html')