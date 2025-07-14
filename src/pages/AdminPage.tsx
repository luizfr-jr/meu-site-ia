import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardBody,
  Button,
  Input,
  Textarea,
  Select,
  SelectItem,
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  useDisclosure,
  Chip
} from '@heroui/react';
import { Plus, Edit, Trash2, LogOut, Settings, Home } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { initialIAs, categories } from '../data/ias';
import type { IAData } from '../types';

const AdminPage: React.FC = () => {
  const [ias, setIAs] = useState<IAData[]>(initialIAs);
  const [editingIA, setEditingIA] = useState<IAData | null>(null);
  const [formData, setFormData] = useState<Partial<IAData>>({});
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { logout, user } = useAuth();
  const navigate = useNavigate();

  // Redirect se não estiver autenticado
  useEffect(() => {
    if (!user) {
      navigate('/admin/login');
    }
  }, [user, navigate]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const handleAddNew = () => {
    setEditingIA(null);
    setFormData({
      name: '',
      description: '',
      image: '',
      url: '',
      category: '',
      tags: []
    });
    onOpen();
  };

  const handleEdit = (ia: IAData) => {
    setEditingIA(ia);
    setFormData({
      ...ia,
      tags: ia.tags
    });
    onOpen();
  };

  const handleDelete = (id: string) => {
    setIAs(prev => prev.filter(ia => ia.id !== id));
  };

  const handleSave = () => {
    if (!formData.name || !formData.description || !formData.url || !formData.category) {
      alert('Por favor, preencha todos os campos obrigatórios.');
      return;
    }

    const now = new Date();
    const tags = typeof formData.tags === 'string'
      ? (formData.tags as string).split(',').map((tag: string) => tag.trim()).filter((tag: string) => tag)
      : (formData.tags as string[]) || [];

    if (editingIA) {
      // Editar existente
      setIAs(prev => prev.map(ia => 
        ia.id === editingIA.id 
          ? {
              ...ia,
              ...formData,
              tags,
              updatedAt: now
            } as IAData
          : ia
      ));
    } else {
      // Adicionar novo
      const newIA: IAData = {
        id: Date.now().toString(),
        name: formData.name!,
        description: formData.description!,
        image: formData.image || '/Img/default.png',
        url: formData.url!,
        category: formData.category!,
        tags,
        createdAt: now,
        updatedAt: now
      };
      setIAs(prev => [...prev, newIA]);
    }

    onClose();
  };

  const handleInputChange = (field: keyof IAData, value: string | string[]) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (!user) {
    return null; // Será redirecionado
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Settings className="w-8 h-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Painel Administrativo</h1>
                <p className="text-gray-600">Gerenciar ferramentas de IA</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                as="a"
                href="/"
                variant="light"
                startContent={<Home className="w-4 h-4" />}
              >
                Ver Site
              </Button>
              <Button
                color="danger"
                variant="light"
                onClick={handleLogout}
                startContent={<LogOut className="w-4 h-4" />}
              >
                Sair
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Ferramentas de IA ({ias.length})
            </h2>
            <p className="text-gray-600 mt-1">
              Gerencie todas as ferramentas disponíveis no site
            </p>
          </div>
          <Button
            color="primary"
            onClick={handleAddNew}
            startContent={<Plus className="w-4 h-4" />}
          >
            Adicionar Nova
          </Button>
        </div>

        <Card>
          <CardBody className="p-0">
            <Table aria-label="Tabela de ferramentas de IA">
              <TableHeader>
                <TableColumn>NOME</TableColumn>
                <TableColumn>CATEGORIA</TableColumn>
                <TableColumn>DESCRIÇÃO</TableColumn>
                <TableColumn>TAGS</TableColumn>
                <TableColumn>AÇÕES</TableColumn>
              </TableHeader>
              <TableBody>
                {ias.map((ia) => (
                  <TableRow key={ia.id}>
                    <TableCell>
                      <div className="flex items-center space-x-3">
                        <img
                          src={ia.image}
                          alt={ia.name}
                          className="w-8 h-8 rounded object-cover"
                        />
                        <div>
                          <p className="font-medium text-gray-900">{ia.name}</p>
                          <p className="text-sm text-gray-500">{ia.url}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Chip size="sm" color="primary" variant="flat">
                        {ia.category}
                      </Chip>
                    </TableCell>
                    <TableCell>
                      <p className="text-sm text-gray-600 max-w-xs truncate">
                        {ia.description}
                      </p>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {ia.tags.slice(0, 2).map((tag, index) => (
                          <Chip key={index} size="sm" variant="flat" color="secondary">
                            {tag}
                          </Chip>
                        ))}
                        {ia.tags.length > 2 && (
                          <Chip size="sm" variant="flat" color="default">
                            +{ia.tags.length - 2}
                          </Chip>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Button
                          size="sm"
                          variant="light"
                          color="primary"
                          onClick={() => handleEdit(ia)}
                          startContent={<Edit className="w-4 h-4" />}
                        >
                          Editar
                        </Button>
                        <Button
                          size="sm"
                          variant="light"
                          color="danger"
                          onClick={() => handleDelete(ia.id)}
                          startContent={<Trash2 className="w-4 h-4" />}
                        >
                          Excluir
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardBody>
        </Card>
      </div>

      {/* Modal para Adicionar/Editar */}
      <Modal isOpen={isOpen} onClose={onClose} size="2xl">
        <ModalContent>
          <ModalHeader className="flex flex-col gap-1">
            {editingIA ? 'Editar Ferramenta' : 'Adicionar Nova Ferramenta'}
          </ModalHeader>
          <ModalBody>
            <div className="space-y-4">
              <Input
                label="Nome"
                placeholder="Nome da ferramenta"
                value={formData.name || ''}
                onChange={(e) => handleInputChange('name', e.target.value)}
                required
              />
              
              <Textarea
                label="Descrição"
                placeholder="Descrição da ferramenta"
                value={formData.description || ''}
                onChange={(e) => handleInputChange('description', e.target.value)}
                required
              />
              
              <Input
                label="URL"
                placeholder="https://exemplo.com"
                value={formData.url || ''}
                onChange={(e) => handleInputChange('url', e.target.value)}
                required
              />
              
              <Input
                label="Imagem (URL)"
                placeholder="/Img/exemplo.png"
                value={formData.image || ''}
                onChange={(e) => handleInputChange('image', e.target.value)}
              />
              
              <Select
                label="Categoria"
                placeholder="Selecione uma categoria"
                selectedKeys={formData.category ? [formData.category] : []}
                onSelectionChange={(keys) => {
                  const selectedKey = Array.from(keys)[0] as string;
                  handleInputChange('category', selectedKey);
                }}
              >
                {categories.map((category) => (
                  <SelectItem key={category}>
                    {category}
                  </SelectItem>
                ))}
              </Select>
              
              <Input
                label="Tags (separadas por vírgula)"
                placeholder="tag1, tag2, tag3"
                value={Array.isArray(formData.tags) ? formData.tags.join(', ') : formData.tags || ''}
                onChange={(e) => handleInputChange('tags', e.target.value)}
              />
            </div>
          </ModalBody>
          <ModalFooter>
            <Button color="danger" variant="light" onPress={onClose}>
              Cancelar
            </Button>
            <Button color="primary" onPress={handleSave}>
              {editingIA ? 'Salvar Alterações' : 'Adicionar Ferramenta'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </div>
  );
};

export default AdminPage;