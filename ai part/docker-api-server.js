const express = require('express');
const { exec } = require('child_process');
const cors = require('cors');
const app = express();
const port = 3000;

// 启用CORS
app.use(cors());
app.use(express.json());

// 健康检查端�?app.get('/health', (req, res) => {
  res.json({ status: 'ok', message: 'Docker API服务器正常运�? });
});

// 获取所有容器状�?app.get('/api/docker/status', (req, res) => {
  exec('docker ps -a --format "{{.Names}},{{.Status}},{{.Ports}}"', (error, stdout, stderr) => {
    if (error) {
      console.error(`执行命令出错: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '获取容器状态失�?,
        data: null
      });
    }
    
    const containers = stdout.trim().split('\n')
      .filter(line => line.trim() !== '')
      .map(line => {
        const [name, status, ports] = line.split(',');
        return { name, status, ports };
      });
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '获取容器状态成�?,
      data: containers
    });
  });
});

// 启动SQL注入实验容器
app.post('/api/docker/start-sqli', (req, res) => {
  exec('cd sqli-lab && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动SQL注入实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动SQL注入实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: 'SQL注入实验容器启动成功',
      data: { url: 'http://192.168.1.106:8091/index.php' }
    });
  });
});

// 启动XSS实验容器
app.post('/api/docker/start-xss', (req, res) => {
  exec('cd xss-lab && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动XSS实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动XSS实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: 'XSS实验容器启动成功',
      data: { url: 'http://192.168.1.106:8092/index.php' }
    });
  });
});

// 启动CSRF实验容器
app.post('/api/docker/start-csrf', (req, res) => {
  exec('cd csrf-lab && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动CSRF实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动CSRF实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: 'CSRF实验容器启动成功',
      data: { url: 'http://192.168.1.106:8093/index.php' }
    });
  });
});

// 启动命令注入实验容器
app.post('/api/docker/start-cmd', (req, res) => {
  exec('cd command-inject && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动命令注入实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动命令注入实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '命令注入实验容器启动成功',
      data: { url: 'http://192.168.1.106:8090/index.html' }
    });
  });
});

// 启动文件上传实验容器
app.post('/api/docker/start-upload', (req, res) => {
  exec('cd file-upload-lab && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动文件上传实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动文件上传实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '文件上传实验容器启动成功',
      data: { url: 'http://192.168.1.106:8094/index.php' }
    });
  });
});

// 启动目录遍历实验容器
app.post('/api/docker/start-dir', (req, res) => {
  exec('cd directory-traversal-lab && docker-compose up -d', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动目录遍历实验容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动目录遍历实验容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '目录遍历实验容器启动成功',
      data: { url: 'http://192.168.1.106:8095/index.php' }
    });
  });
});

// 启动安全代码容器
app.post('/api/docker/start-sec-code', (req, res) => {
  exec('docker run -d --name sec-code-container -p 8080:80 gsycl2004/sec-code', (error, stdout, stderr) => {
    if (error) {
      console.error(`启动安全代码容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '启动安全代码容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '安全代码容器启动成功',
      data: { url: 'http://192.168.1.106:8080' }
    });
  });
});

// 停止所有实验容器
app.post('/api/docker/stop-all', (req, res) => {
  exec('cd seclab && .\\stop-all-services.bat', (error, stdout, stderr) => {
    if (error) {
      console.error(`停止所有容器失败: ${error}`);
      return res.status(500).json({ 
        isSuccess: 0,
        status: 500,
        message: '停止所有容器失败',
        data: null
      });
    }
    
    res.json({ 
      isSuccess: 1,
      status: 200,
      message: '所有容器已停止',
      data: null
    });
  });
});

// 获取容器列表
app.get('/api/docker/list', (req, res) => {
  exec('docker ps -a --format "{{.Names}},{{.Status}}"', (error, stdout, stderr) => {
    if (error) {
      console.error(`获取容器列表失败: ${error}`);
      return res.status(500).json({
        success: false,
        error: '获取容器列表失败'
      });
    }
    
    const containers = stdout.trim().split('\n')
      .filter(line => line.trim() !== '')
      .map(line => {
        const [name, status] = line.split(',');
        return { name, status };
      });
    
    res.json({ success: true, data: containers });
  });
});

// 获取指定容器详情
app.get('/api/docker/containers', (req, res) => {
  const name = req.query.name;
  if (name) {
    exec(`docker inspect --format "{{.Name}},{{.State.Status}},{{.State.StartedAt}}" ${name}`, (error, stdout, stderr) => {
      if (error) {
        return res.status(404).json({ success: false, error: `容器 '${name}' 不存在` });
      }
      const [cName, status, startedAt] = stdout.trim().split(',');
      res.json({ success: true, data: { name: cName.replace(/^\//, ''), status, started_at: startedAt } });
    });
  } else {
    exec('docker ps -a --format "{{.Names}},{{.Status}}"', (error, stdout, stderr) => {
      if (error) {
        return res.status(500).json({ success: false, error: '获取容器列表失败' });
      }
      const containers = stdout.trim().split('\n')
        .filter(line => line.trim() !== '')
        .map(line => {
          const [name, status] = line.split(',');
          return { name, status };
        });
      res.json({ success: true, data: containers });
    });
  }
});

// 获取容器日志
app.get('/api/docker/logs/:container_name', (req, res) => {
  const containerName = req.params.container_name;
  const tail = req.query.tail || 100;
  exec(`docker logs --tail ${tail} ${containerName}`, (error, stdout, stderr) => {
    if (error) {
      return res.status(404).json({ success: false, error: `容器 '${containerName}' 不存在或未运行` });
    }
    res.json({ success: true, container: containerName, logs: stdout + stderr });
  });
});

// 在容器内执行命令
app.post('/api/docker/exec/:container_name', (req, res) => {
  const containerName = req.params.container_name;
  const command = req.body.command;
  if (!command) {
    return res.status(400).json({ success: false, error: '缺少 command 参数' });
  }
  exec(`docker exec ${containerName} ${command}`, (error, stdout, stderr) => {
    if (error) {
      return res.status(500).json({ 
        success: false, 
        error: stderr || error.message 
      });
    }
    res.json({ 
      success: true, 
      container: containerName, 
      command: command,
      exit_code: 0,
      output: stdout + stderr 
    });
  });
});

// 停止指定容器
app.post('/api/docker/stop/:container_name', (req, res) => {
  const containerName = req.params.container_name;
  exec(`docker stop ${containerName}`, (error, stdout, stderr) => {
    if (error) {
      console.error(`停止容器失败: ${error}`);
      return res.status(500).json({ 
        success: false, 
        error: `停止容器 '${containerName}' 失败: ${stderr || error.message}` 
      });
    }
    res.json({ 
      success: true, 
      message: `容器 '${containerName}' 已停止` 
    });
  });
});

// 启动指定容器
app.post('/api/docker/start/:container_name', (req, res) => {
  const containerName = req.params.container_name;
  exec(`docker start ${containerName}`, (error, stdout, stderr) => {
    if (error) {
      console.error(`启动容器失败: ${error}`);
      return res.status(500).json({ 
        success: false, 
        error: `启动容器 '${containerName}' 失败: ${stderr || error.message}` 
      });
    }
    res.json({ 
      success: true, 
      message: `容器 '${containerName}' 已启动` 
    });
  });
});

// 启动服务�?app.listen(port, () => {
  console.log(`Docker API服务器运行在 http://192.168.1.106:${port}`);
}); 
