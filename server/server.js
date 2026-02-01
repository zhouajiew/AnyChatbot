const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const { profile } = require('console');
const app = express();

const port = 1314;

var error_info = "";

app.use(cors());

// 配置Multer存储
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, 'uploads/'); // 指定文件上传目录
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname); // 重命名文件
  }
});

// 创建Multer实例
const upload = multer({
  storage: storage,
  limits: { fileSize: 5 * 1024 * 1024 }, // 限制文件大小为5MB
  fileFilter: (req, file, cb) => {
    const filetypes = /jpeg|jpg|png/; // 支持的文件类型
    const mimetype = filetypes.test(file.mimetype);
    const extname = filetypes.test(path.extname(file.originalname).toLowerCase());
    if (mimetype && extname) {
      return cb(null, true);
    }
    error_info = "不支持的文件类型！"
    cb("不支持的文件类型！", false);
  }
})

app.get('/get-profile1/:user_name',function(req,res){
  /*
  查询参数 req.query.name /...?
  路由参数 req.param.id   /...
  */
  var user_name = req.params.user_name;
  var s = false;

  console.log(`用户${user_name}的获取头像请求`);

  type_list = ['jpg','jpeg','png'];

  type_list.forEach(t => {
      if (fs.existsSync(`${process.cwd()}/uploads/${user_name}.${t}`)){
        res.sendFile(`${process.cwd()}/uploads/${user_name}.${t}`);
        s = true; 
      }     
  });

  if (!s){
    error_info = '没有获取到该用户的头像！';
    return res.status(400).json({error: error_info});
  }   
})

app.get('/get-profile2/:assistant_name',function(req,res){
  /*
  查询参数 req.query.name /...?
  路由参数 req.param.id   /...
  */
  var assistant_name = req.params.assistant_name;
  var s = false;
  console.log(`获取助理${assistant_name}的头像请求`);

  type_list = ['jpg','jpeg','png'];

  type_list.forEach(t => {
      if (fs.existsSync(`${process.cwd()}/uploads/${assistant_name}.${t}`)){
        res.sendFile(`${process.cwd()}/uploads/${assistant_name}.${t}`); 
        s = true;
      }     
  });

  if (!s){
    error_info = '没有获取助理的头像！';
    return res.status(400).json({error: error_info});
  }   
})

// 单文件上传(上传用户头像)
app.post('/upload/single', function(req, res){
  upload.single('file')(req, res, function (err) {
    if (err instanceof multer.MulterError) {
      console.log(err, 'multer error');
      return res.status(400).json({error: err.message});
    } else if (err) {
      console.log('normal error', error_info);
      return res.status(400).json({error: error_info});
    }

    var file_name = "";
    var file_type = "";
    var user_name = req.body.user_name;

    let pattern = /([\s\S]*)\.([\s\S]*)/;
    var match = pattern.exec(req.file.originalname);

    if (match){
        file_name = match[1];
        file_type = match[2];
    }

    // 旧的文件路径
    const oldPath = path.join(process.cwd(), `/uploads/${req.file.originalname}`);
    // 新的文件路径
    const newPath = path.join(process.cwd(), `/uploads/${user_name}.${file_type}`);

    type_list = ['jpg','jpeg','png'];

    type_list.forEach(t => {
        if (fs.existsSync(`${process.cwd()}/uploads/${user_name}.${t}`)){
            fs.unlink(`${process.cwd()}/uploads/${user_name}.${t}`, (err) => {
            if (err) throw err;
            console.log(`已成功删除文件uploads/${user_name}.${t}`);
            });   
        }     
    });

    type_list.forEach(t => {
        if (fs.existsSync(`../build/static/media/${user_name}.${t}`)){
            fs.unlink(`${process.cwd()}/uploads/${user_name}.${t}`, (err) => {
            if (err) throw err;
            console.log(`已成功删除文件${user_name}.${t}`);
            });   
        }     
    });

    // 使用fs.rename()重命名文件
    fs.rename(oldPath, newPath, (err) => {
        if (err) throw err;
        console.log('文件已成功重命名！');
        /*
        const sourceFile = newPath;
        const destinationFile = file1_path;
      
        fs.copyFile(sourceFile, destinationFile, (err) => {
          if (err) throw err;
          console.log('文件复制成功');
        });
        */
    });    


    // 没有错误 
    res.json({
        message: '文件上传成功',
        file: {
        filename: req.file.filename,
        originalname: req.file.originalname,
        size: req.file.size,
        path: req.file.path
        },
    });   
  })
});

// 单文件上传(上传助理头像)
app.post('/upload/single2', function(req, res){
  upload.single('file')(req, res, function (err) {
    if (err instanceof multer.MulterError) {
      console.log(err, 'multer error'); 
      return res.status(400).json({error: err.message});
    } else if (err) {
      console.log('normal error', error_info);
      return res.status(400).json({error: error_info});
    }

    var file_name = "";
    var file_type = "";
    var assistant_name = req.body.assistant_name;

    let pattern = /([\s\S]*)\.([\s\S]*)/;
    var match = pattern.exec(req.file.originalname);

    if (match){
        file_name = match[1];
        file_type = match[2];
    }

    // 旧的文件路径
    const oldPath = path.join(process.cwd(), `/uploads/${req.file.originalname}`);
    // 新的文件路径
    const newPath = path.join(process.cwd(), `/uploads/${assistant_name}.${file_type}`);

    type_list = ['jpg','jpeg','png'];

    type_list.forEach(t => {
        if (fs.existsSync(`${process.cwd()}/uploads/${assistant_name}.${t}`)){
            fs.unlink(`${process.cwd()}/uploads/${assistant_name}.${t}`, (err) => {
            if (err) throw err;
            console.log(`已成功删除文件uploads/${assistant_name}.${t}`);
            });   
        }     
    });

    type_list.forEach(t => {
        if (fs.existsSync(`../build/static/media/${assistant_name}.${t}`)){
            fs.unlink(`${process.cwd()}/uploads/${assistant_name}.${t}`, (err) => {
            if (err) throw err;
            console.log(`已成功删除文件${assistant_name}.${t}`);
            });   
        }     
    });

    // 使用fs.rename()重命名文件
    fs.rename(oldPath, newPath, (err) => {
        if (err) throw err;
        console.log('文件已成功重命名！');
        /*
        const sourceFile = newPath;
        const destinationFile = file1_path;
      
        fs.copyFile(sourceFile, destinationFile, (err) => {
          if (err) throw err;
          console.log('文件复制成功');
        });
        */
    });    


    // 没有错误 
    res.json({
        message: '文件上传成功',
        file: {
        filename: req.file.filename,
        originalname: req.file.originalname,
        size: req.file.size,
        path: req.file.path
        },
    });   
  })
});

// 多文件上传
app.post('/upload/multiple', upload.array('files', 5), (req, res) => {
  if (!req.files || req.files.length === 0) {
    return res.status(400).json({ error: '没有文件上传' });
  }
  
  const files = req.files.map(file => ({
    filename: file.filename,
    originalname: file.originalname,
    size: file.size,
    path: file.path
  }));
  
  res.json({
    message: '文件上传成功',
    files: files
  });
});

// 混合字段上传
const uploadFields = upload.fields([
  { name: 'avatar', maxCount: 1 },
  { name: 'gallery', maxCount: 8 }
]);

app.post('/upload/fields', uploadFields, (req, res) => {
  res.json({
    message: '文件上传成功',
    files: req.files,
    body: req.body
  });
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});

// pkg server.js --targets node18 --platform=all --output=server
