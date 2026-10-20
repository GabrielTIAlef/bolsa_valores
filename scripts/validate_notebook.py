"""Executa o notebook em kernel temporário do Python atual; não altera kernels globais."""
import json
import os
from pathlib import Path
import sys
import tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / '.local-test'
    output.mkdir(exist_ok=True)
    result_path = output / 'notebook-result.json'
    result_path.unlink(missing_ok=True)
    notebook = nbformat.read(ROOT / 'notebooks/analise_temporal.ipynb', as_version=4)
    with tempfile.TemporaryDirectory(prefix='bolsa-kernel-') as directory:
        directory = Path(directory)
        spec = directory / 'kernels/bolsa-local'
        spec.mkdir(parents=True)
        (spec / 'kernel.json').write_text(json.dumps({
            'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Bolsa validation', 'language': 'python'}), encoding='utf-8')
        manager = KernelManager(kernel_name='bolsa-local',
                                kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(spec.parent)]))
        env = dict(os.environ, BOLSA_NOTEBOOK_OUTPUT=str(directory / 'outputs'),
                   IPYTHONDIR=str(directory / 'ipython'), JUPYTER_RUNTIME_DIR=str(directory / 'runtime'),
                   MPLCONFIGDIR=str(directory / 'matplotlib'), PYTHONUTF8='1')
        try:
            NotebookClient(notebook, km=manager, timeout=180,
                           resources={'metadata': {'path': str(ROOT)}}).execute(env=env)
        finally:
            # Um manager injetado pertence ao chamador, não ao NotebookClient.
            if manager.has_kernel:
                manager.shutdown_kernel(now=True)
            manager.cleanup_resources()
        cells = sum(cell.cell_type == 'code' for cell in notebook.cells)
        confirmed = (directory / 'outputs/latest.json').exists()
        if not confirmed:
            raise RuntimeError('Notebook não publicou a demonstração.')
        result = {'code_cells': cells, 'successful': True, 'synthetic_publication': confirmed}
    result_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
